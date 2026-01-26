import collections
import os
import re
import string
import textwrap

import numpy as np

import py_misc_utils.alog as alog
import py_misc_utils.module_utils as pymu
import py_misc_utils.template_replace as pytr
import py_misc_utils.utils as pyu

from .decorators import *
from .entity import *
from .pyxhdl import *
from .types import *
from .vars import *
from .utils import *
from .wrap import *

from . import xlib as XL


TbData = collections.namedtuple('TbData', 'inputs, outputs, wait, wait_expr, env')


class _TestData:

  def __init__(self, path, eclass):
    self._data = pyu.load_config(path)
    self._conf = self._data.get('conf', dict())
    self._env = self._data.get('env', dict())
    self._loaders = self._conf.get('loaders', dict())

    inp, outp = dict(), dict()
    for pin in eclass.PORTS:
      if pin.is_rd():
        inp[pin.name] = pin
      if pin.is_wr():
        outp[pin.name] = pin

    self._inp, self._outp = inp, outp

  def conf(self, *cpath, defval=None):
    return pyu.dict_rget(self._conf, cpath, defval=defval)

  def setenv(self, name, value):
    self._env[name] = value

  def _load(self, name, value):
    loader = self.conf('loaders', name)
    if loader is not None:
      kind = loader.get('kind')
      if kind == 'numpy':
        return np.array(value, dtype=loader.get('dtype'))
      else:
        alog.warning(f'Unknown loader kind: {kind}')

    return value

  def __iter__(self):
    for data in self._data.get('data', ()):
      inputs, outputs = dict(), dict()
      for k, v in data.items():
        if k in self._inp:
          inputs[k] = self._load(k, v)
        if k in self._outp:
          outputs[k] = self._load(k, v)

      wait = data.get('_wait')
      wait_expr = data.get('_wait_expr')

      yield TbData(inputs=inputs,
                   outputs=outputs,
                   wait=wait,
                   wait_expr=wait_expr,
                   env=self._env)


class _Required:
  pass


_REQUIRED = _Required()

_STD_TOLL = 1e-5

_TB_ARGS = dict(
  input_file=_REQUIRED,
  wait=None,
  clock=[],
  clock_sync=None,
  write_output=False,
  toll=_STD_TOLL,
)


def add_arguments(parser):
  parser.add_argument('--tb_input_file', type=str,
                      help='The testbench input file')
  parser.add_argument('--tb_wait', type=int,
                      help='The amount of wait after setting the inputs, to emit the output')
  parser.add_argument('--tb_clock', type=str, action='append',
                      help='The name and period of the clock input (NAME,PERIOD)')
  parser.add_argument('--tb_clock_sync', type=str,
                      help='The edge of the clock to sync the data feed with')
  parser.add_argument('--tb_write_output', action='store_true',
                      help='Whether a write to STDOUT should be generated for every input')
  parser.add_argument('--tb_toll', type=float,
                      help='The tollerance in comparing floating point values')


def _make_args(args):
  tb_args = dict()
  for name, value in _TB_ARGS.items():
    aname = f'tb_{name}'
    avalue = getattr(args, aname, None)
    if avalue is None:
      if value is _REQUIRED:
        pyu.fatal(f'Missing command line argument: --{aname}')
      else:
        avalue = value

    tb_args[name] = avalue

  return tb_args


def _get_write_string(eclass, inputs, chunksize=5):
  wparts = []
  for pin in eclass.PORTS:
    dtype = inputs[pin.name].dtype
    if len(dtype.array_shape) > 0:
      for idx in np.ndindex(dtype.array_shape):
        substr = ', '.join(str(x) for x in idx)

        wparts.append(f'{pin.name}[{substr}]={{{pin.name}[{substr}]}}')
    else:
      wparts.append(f'{pin.name}={{{pin.name}}}')

  chunks = [wparts[i: i + chunksize] for i in range(0, len(wparts), chunksize)]
  writes = ['TIME={NOW} ' + ' '.join(chunks[0])]
  for wp in chunks[1: ]:
    writes.append('    ' + ' '.join(wp))

  return '\n'.join(writes)


def _gen_wait(data, wait, clock, clock_sync, eclass, env):
  rwait = data.wait or wait
  if rwait:
    XL.wait_for(rwait)

  if clock_sync == 'rising':
    XL.wait_rising(XL.load(clock))
  elif clock_sync == 'falling':
    XL.wait_falling(XL.load(clock))

  if data.wait_expr is not None:
    wexpr = data.wait_expr.replace(';', '\n')
    XL.xexec(wexpr, **env)


def _repr(v, dtype):
  if isinstance(dtype, Bool):
    return 'true' if v else 'false'

  if isinstance(dtype, Bits):
    fmt = f'{{v:0{dtype.nbits}b}}'
    return fmt.format(v=v)

  if isinstance(dtype, (Sint, Uint)):
    nibbles = (dtype.nbits + 1) // 4
    fmt = f'{{v:0{nibbles}X}}'
    return fmt.format(v=v)

  return v


Clock = collections.namedtuple('Clock', 'name, period')

def _parse_clocks(args):
  clocks = []
  for clk in args['clock']:
    name, period = pyu.resplit(clk, ',')

    clocks.append(Clock(name=name, period=int(period)))

  return clocks


@hdl
def _assign_value(var, value):
  code = []
  if isinstance(value, np.ndarray):
    shape = var.dtype.array_shape
    if tuple(shape) != tuple(value.shape):
      pyu.fatal(f'Wrong shape for "{var.ref.name}": {tuple(shape)} vs {tuple(value.shape)}')

    for idx in np.ndindex(shape):
      substr = ', '.join(str(x) for x in idx)
      code.append(f'{var.ref.name}[{substr}] = {value[idx]}')
  else:
    code.append(f'{var.ref.name} = {value}')

  XL.xexec('\n'.join(code))


@hdl
def _values_differ(value, ref_value, toll):
  if isinstance(value.dtype, Float):
    return not XL.float_equal(value, ref_value, _STD_TOLL if toll is None else toll)

  return value != ref_value


@hdl
def _compare_value(var, value, toll=None):
  if isinstance(value, np.ndarray):
    shape = var.dtype.array_shape
    if tuple(shape) != tuple(value.shape):
      pyu.fatal(f'Wrong shape for "{var.ref.name}": {tuple(shape)} vs {tuple(value.shape)}')

    for idx in np.ndindex(shape):
      substr = ', '.join(str(x) for x in idx)
      astr = f'{var.ref.name}[{substr}]'
      tmp = XL.load(astr)
      if _values_differ(tmp, value[idx].item(), toll=toll):
        XL.report(f'{{NOW}} Output mismatch: {astr} = {{{astr}}} (should be {_repr(value[idx], tmp.dtype)})')
  else:
    tmp = XL.load(var.ref.name)
    if _values_differ(tmp, value, toll=toll):
      XL.report(f'{{NOW}} Output mismatch: {var.ref.name} = {{{var.ref.name}}} (should be {_repr(value, tmp.dtype)})')


class TestBench(Entity):

  PORTS = tuple()
  ARGS = dict(args=None)

  def __init__(self, eclass, inputs, args, **kwargs):
    super().__init__(**kwargs)
    self._eclass = eclass
    self._inputs = inputs
    self._tbargs = args
    self._clocks = _parse_clocks(args)

  def _input_data(self):
    _, ext = os.path.splitext(self._tbargs['input_file'])
    if ext == '.py':
      mod = pymu.load_module(self._tbargs['input_file'])

      return mod.tb_iterator(self._eclass, self._inputs, self._tbargs,
                             clocks=self._clocks)
    else:
      tbdata = _TestData(self._tbargs['input_file'], self._eclass)

      return tbdata

  @hdl_process(kind=INIT_PROCESS)
  def init(self):
    for pin in self._eclass.PORTS:
      XL.assign(pin.name, inputs[pin.name])

  @hdl_process(kind=ROOT_PROCESS)
  def root(self):
    eargs = self._inputs.copy()
    for pin in self._eclass.PORTS:
      eargs[pin.name] = XL.load(pin.name)

    # Instantiate the entity under test.
    ent = self._eclass(**eargs)

  @hdl_process()
  def test(self):
    wait = self._tbargs['wait']
    clock_sync = self._tbargs['clock_sync']
    if clock_sync:
      clock, clock_sync = pyu.resplit(clock_sync, ',')
    else:
      clock = None

    write_string = (_get_write_string(self._eclass, self._inputs)
                    if self._tbargs['write_output'] else None)

    for data in self._input_data():
      for dk, dv in data.inputs.items():
        _assign_value(XL.load(dk), dv)

      _gen_wait(data, wait, clock, clock_sync, self._eclass, data.env)

      if write_string is not None and (data.inputs or data.outputs):
        for wstr in write_string.split('\n'):
          XL.write(wstr)

      for dk, dv in data.outputs.items():
        _compare_value(XL.load(dk), dv, toll=args['toll'])

    XL.finish()

  _CLOCK_FN = """
    @hdl_process()
    def $clock_fn(self):
      $clk_name = not $clk_name
      XL.wait_for($period // 2)
  """

  def enum_processes(self):
    for pfn in super().enum_processes():
      yield pfn

    env = globals().copy()
    for clk in self._clocks:
      alog.debug(f'Generating clock "{clk.name}" with period {clk.period}')

      clock_fn = f'clock_{clk.name}'
      scode = pytr.template_replace(textwrap.dedent(self._CLOCK_FN),
                                    vals=dict(clock_fn=clock_fn,
                                              clk_name=clk.name,
                                              period=clk.period,
                                              ))

      pfn, = pyu.compile(scode, clock_fn, env=env)

      # The inspect API is not able to find the source code information required
      # by the pyxhdl module when using exec(), so we need to provide them here.
      set_function_info(pfn.__wrapped__, __file__, 1, scode)

      yield pfn


def generate(codegen, args, eclass, inputs):
  tb_args = dict(args=_make_args(args), eclass=eclass, inputs=inputs)

  codegen.generate_entity(TestBench, tb_args)

