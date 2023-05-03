import ast
import collections
import functools
import inspect
import logging
import os
import re

import numpy as np

import py_misc_utils.fp_utils as pyf
import py_misc_utils.utils as pyu

from .entity import *
from .emitter import *
from .pyxhdl import *
from .types import *
from .utils import *
from .vars import *
from .wrap import *


_SVMod = collections.namedtuple('SVMod', 'mod, fnname')

_FPU_FNMAP = {
  'add': _SVMod('fpu', 'add'),
  'sub': _SVMod('fpu', 'sub'),
  'mul': _SVMod('fpu', 'mul'),
  'div': _SVMod('fpu', 'div'),
  'mod': _SVMod('fpu', 'mod'),
  'neg': _SVMod('fpu', 'neg'),
  'to_integer': _SVMod('fpu', 'to_integer'),
  'from_integer': _SVMod('fpu', 'from_integer'),
  'one': _SVMod('fpu', 'one'),
  'zero': _SVMod('fpu', 'zero'),
  'from_real': _SVMod('fp_utils', 'from_real'),
  'to_real': _SVMod('fp_utils', 'to_real'),
  'convert': _SVMod('fp_conv', 'convert'),
}

_LOGIC_REMAP = dict(zip('01XUZWHL', '01xxzx10'))

# Describe which Python types can be fed directly to Verilog operators on the
# types in the dictionary values set.
_ARITH_CTYPE_NOCAST = {
  int: {Uint, Sint, Real, Integer},
  float: {Real},
}

_OPSYMS = {
  ast.Add: OpSym('+'),
  ast.Sub: OpSym('-'),
  ast.Mult: OpSym('*'),
  ast.Div: OpSym('/'),
  ast.Mod: OpSym('%'),
  ast.BitOr: OpSym('|'),
  ast.BitXor: OpSym('^'),
  ast.BitAnd: OpSym('&'),
  ast.MatMult: OpSym('&'),
  ast.Eq: OpSym('=='),
  ast.NotEq: OpSym('!='),
  ast.Lt: OpSym('<'),
  ast.LtE: OpSym('<='),
  ast.Gt: OpSym('>'),
  ast.GtE: OpSym('>='),
  ast.LShift: OpSym('<<'),
  ast.RShift: OpSym('>>'),
}

_FLOAT_OPFNS = {
  ast.Add: 'add',
  ast.Sub: 'sub',
  ast.Mult: 'mul',
  ast.Div: 'div',
  ast.Mod: 'mod',
}


_WireReg = collections.namedtuple('WireReg', 'wire, reg, init', defaults=[None])

class _WireRegs(object):

  def __init__(self):
    self._wregs = dict()

  def reg_items(self):
    return self._wregs.items()

  def register(self, var, init=None):
    ref = var.ref
    wreg = self._wregs.get(ref.name, None)
    if wreg is None:
      reg = Register(var.dtype, value=Ref(f'{ref.name}_', vspec=ref.vspec))
      wreg = _WireReg(wire=var, reg=reg, init=init)
      self._wregs[ref.name] = wreg

    return wreg


class _Instance(object):

  def __init__(self, name, params, args):
    self.name = name
    self.params = params
    self.args = args
    self.hash = pyu.genhash((name, params, args))

  def __hash__(self):
    return self.hash

  def __eq__(self, other):
    return (self.name == other.name and self.params == other.params and
            self.args == other.args)


class _Instanciator(object):

  def __init__(self):
    self._instances = dict()
    self._iids = dict()

  def _cname(self, name):
    cname = re.sub(r'[.$:]+', '_', name)

    return cname

  def getid(self, name, **kwargs):
    params = kwargs.pop(PARAM_KEY, dict())
    inst = _Instance(name, params, kwargs)
    iid = self._instances.get(inst, None)
    if iid is None:
      cname = self._cname(name)
      cid = self._iids.get(cname, 0)
      self._iids[cname] = cid + 1
      iid = f'{cname}_{cid + 1}'

      self._instances[inst] = iid

    return iid

  def __iter__(self):
    for inst, iid in self._instances.items():
      yield iid, inst


class Verilog_Emitter(Emitter):

  def __init__(self, cfg_file=None, **kwargs):
    super().__init__(cfg_file=cfg_file, **kwargs)
    self._mod_comment = None
    self._init_module_places()
    self._module_reset()
    self._extra_libs = set()

  @property
  def kind(self):
    return VERILOG

  @property
  def file_ext(self):
    return '.sv'

  @property
  def eol(self):
    return ';'

  @property
  def module_vars_place(self):
    return self._module_vars_place

  @property
  def process_vars_place(self):
    return self._process_vars_place

  @staticmethod
  def fpmod_resolve(mod_name, fnname, argno, exp_param='NX', mant_param='NM',
                    **kwargs):
    def resolver(ctx, cargs):
      return ctx.emitter._fpmod_resolve(mod_name, fnname, cargs, argno, exp_param,
                                        mant_param, kwargs)

    return resolver

  def _fpmod_resolve(self, mod_name, fnname, cargs, argno, exp_param, mant_param,
                     kwargs):
    fspec = self.float_spec(cargs[argno].dtype)
    margs = pyu.new_with(kwargs, **{exp_param: fspec.exp, mant_param: fspec.mant})
    iid = self._iface_id(mod_name, **margs)

    return f'{iid}.{fnname}'

  def _init_module_places(self):
    self._module_vars_place = self.emit_placement()
    self._modules_place = self.emit_placement()
    self._entity_place = self.emit_placement()

  def _module_reset(self):
    self._mod_comment = None
    self._itor = _Instanciator()
    self._wireregs = _WireRegs()

    self._process_reset()

  def _iface_id(self, mod_name, **kwargs):
    self._extra_libs.add(mod_name)

    # This API instantiates only Verilog interfaces, which takes no arguments
    # (only parameters).
    return self._itor.getid(mod_name, **{PARAM_KEY: kwargs})

  def _get_fpcall(self, fnname, **kwargs):
    fn_map = pyu.dict_rget(self._cfg, 'verilog/fpu_fnmap', defval=_FPU_FNMAP)
    svmod = fn_map.get(fnname, None)
    if svmod is None:
      pyu.fatal(f'Unable to find configuration for FPU function: {fnname}')

    iid = self._iface_id(svmod.mod, **kwargs)

    return f'{iid}.{svmod.fnname}'

  def _type_of(self, dtype, kind=None):
    kind = kind or 'logic'
    nbits, shape = dtype.nbits, dtype.array_shape

    adims = ''.join(f'[{x}]' for x in shape)
    if isinstance(dtype, Uint):
      if shape:
        return f'{kind} [{nbits - 1}: 0] {{}}{adims}'
      else:
        return f'{kind} [{nbits - 1}: 0] {{}}'
    elif isinstance(dtype, Sint):
      if shape:
        return f'{kind} signed [{nbits - 1}: 0] {{}}{adims}'
      else:
        return f'{kind} signed [{nbits - 1}: 0] {{}}'
    elif isinstance(dtype, Bits):
      if nbits == 1:
        return f'{kind} {{}}{adims}' if shape else f'{kind} {{}}'

      if shape:
        return f'{kind} [{nbits - 1}: 0] {{}}{adims}'
      else:
        return f'{kind} [{nbits - 1}: 0] {{}}'
    elif isinstance(dtype, Bool):
      return f'{kind} {{}}{adims}' if shape else f'{kind} {{}}'
    elif isinstance(dtype, Integer):
      return f'integer {{}}{adims}' if shape else f'integer {{}}'
    elif isinstance(dtype, Real):
      return f'real {{}}{adims}' if shape else f'real {{}}'
    elif isinstance(dtype, Float):
      fspec = self.float_spec(dtype)
      nfbits = 1 + fspec.exp + fspec.mant
      if shape:
        return f'{kind} [{nfbits - 1}: 0] {{}}{adims}'
      else:
        return f'{kind} [{nfbits - 1}: 0] {{}}'

    pyu.fatal(f'Unknown type: {dtype}', exc=TypeError)

  def _resize_bits(self, value, nbits):
    if value.dtype.nbits == nbits:
      return value

    result = f'{nbits}\'({self.svalue(value)})'

    shape = list(value.dtype.shape)
    shape[-1] = nbits

    return value.new_value(result, shape=shape)

  def _to_bool(self, value, dtype):
    if isinstance(value, Value):
      xvalue = self.svalue(value)
      if isinstance(value.dtype, (Sint, Uint, Bits)):
        return f'&{paren(xvalue)}'

      zero = self._cast(0, value.dtype)
      return f'{paren(xvalue)} != {zero}'

    if isinstance(value, str):
      value = ast.literal_eval(value)

    return '1' if value else '0'

  def _to_int(self, value, dtype, signed):
    itype = 'signed' if signed else 'unsigned'
    if isinstance(value, Value):
      if isinstance(value.dtype, (Uint, Sint)):
        xvalue = self.svalue(self._resize_bits(value, dtype.nbits))
        return f'{itype}\'({xvalue})' if type(dtype) != type(value.dtype) else xvalue
      elif isinstance(value.dtype, Bits):
        xvalue = self.svalue(self._resize_bits(value, dtype.nbits))
        return f'signed\'({xvalue})' if signed else xvalue
      elif isinstance(value.dtype, Float):
        fspec = self.float_spec(dtype)
        fpcall = self._get_fpcall('to_integer', NX=fspec.exp, NM=fspec.mant, NINT=dtype.nbits)
        xvalue = f'{dtype.nbits}\'({fpcall}({self.svalue(value)}))'
        return f'unsigned\'({xvalue})' if not signed else xvalue
      elif isinstance(value.dtype, Integer):
        xvalue = f'{dtype.nbits}\'({self.svalue(value)})'
        return f'unsigned\'({xvalue})' if not signed else xvalue
      elif isinstance(value.dtype, Real):
        xvalue = f'{dtype.nbits}\'($rtoi({self.svalue(value)}))'
        return f'unsigned\'({xvalue})' if not signed else xvalue
      elif isinstance(value.dtype, Bool):
        xvalue = f'{dtype.nbits}\'({self.svalue(value)})'
        return f'signed\'({xvalue})' if signed else xvalue
      else:
        pyu.fatal(f'Unknown type: {value.dtype}', exc=TypeError)

    if isinstance(value, str):
      value = ast.literal_eval(value)

    xvalue = f'{dtype.nbits}\'({int(value)})'
    return f'unsigned\'({xvalue})' if not signed else xvalue

  def _to_uint(self, value, dtype):
    return self._to_int(value, dtype, False)

  def _to_sint(self, value, dtype):
    return self._to_int(value, dtype, True)

  def _try_convert_literal(self, value):
    # This API should not try to convert Python `int` or `float` literals, as those
    # are better off directly going to the cast operators, resulting in less bits
    # resize operations.
    if value is True or value is False:
      return Value(BOOL, value='1' if value else '0')
    if value is None:
      return Value(VOID)
    if isinstance(value, str):
      bstr = self._match_bitstring(value, remap=lambda x: _LOGIC_REMAP[x])
      if bstr is not None:
        nbits = len(bstr)
        return Value(Bits(nbits), value=f'{nbits}\'b{bstr}')

      dtype, ivalue = self._match_intstring(value)
      if dtype is not None:
        if isinstance(dtype, Uint):
          return Value(dtype, value=f'{dtype.nbits}\'({ivalue})')
        else:
          return Value(dtype, value=f'signed\'({dtype.nbits}\'({ivalue}))')

    return value

  def _to_bits(self, value, dtype):
    if isinstance(value, Value):
      if isinstance(value.dtype, (Uint, Sint)):
        xvalue = self.svalue(self._resize_bits(value, dtype.nbits))
        return f'unsigned\'({xvalue})' if isinstance(value.dtype, Sint) else xvalue
      elif isinstance(value.dtype, Bits):
        return self.svalue(self._resize_bits(value, dtype.nbits))
      elif isinstance(value.dtype, Float):
        fspec = self.float_spec(dtype)
        fpcall = self._get_fpcall('to_integer', NX=fspec.exp, NM=fspec.mant, NINT=dtype.nbits)
        return f'unsigned\'({dtype.nbits}\'({fpcall}({self.svalue(value)})))'
      elif isinstance(value.dtype, Integer):
        return f'unsigned\'({dtype.nbits}\'({self.svalue(value)}))'
      elif isinstance(value.dtype, Real):
        return f'unsigned\'({dtype.nbits}\'($rtoi({self.svalue(value)})))'
      elif isinstance(value.dtype, Bool):
        return f'{dtype.nbits}\'({self.svalue(value)})'

    if isinstance(value, str):
      if value.startswith('0b'):
        value = value[2: ]
      if dtype.nbits > len(value):
        bvalue = ('0' * (dtype.nbits - len(value))) + value
      else:
        bvalue = value[-dtype.nbits: ]

      bstr = ''.join(_LOGIC_REMAP[x] for x in bvalue.upper())

      return f'{len(bstr)}\'b{bstr}'

    return f'unsigned\'({dtype.nbits}\'({value}))'

  def _to_float(self, value, dtype):
    fspec = self.float_spec(dtype)
    if isinstance(value, Value):
      if isinstance(value.dtype, (Uint, Sint, Bits)):
        fpcall = self._get_fpcall('from_integer', NX=fspec.exp, NM=fspec.mant, NINT=value.dtype.nbits)
        return f'{fpcall}({self.svalue(value)})'
      elif isinstance(value.dtype, Float):
        ifspec = self.float_spec(value.dtype)
        fpcall = self._get_fpcall('convert', INX=ifspec.exp, INM=ifspec.mant,
                                  ONX=fspec.exp, ONM=fspec.mant)
        return f'{fpcall}({self.svalue(value)})'
      elif isinstance(value.dtype, Integer):
        nbits = max(32, dtype.nbits)
        fpcall = self._get_fpcall('from_integer', NX=fspec.exp, NM=fspec.mant, NINT=nbits)
        return f'{fpcall}({nbits}\'({self.svalue(value)}))'
      elif isinstance(value.dtype, Real):
        fpcall = self._get_fpcall('from_real', NX=fspec.exp, NM=fspec.mant)
        return f'{fpcall}({self.svalue(value)})'
      elif isinstance(value.dtype, Bool):
        fpcall_one = self._get_fpcall('one', NX=fspec.exp, NM=fspec.mant)
        fpcall_zero = self._get_fpcall('zero', NX=fspec.exp, NM=fspec.mant)
        xvalue = self.svalue(value)
        return f'{paren(xvalue)} ? {fpcall_one}() : {fpcall_zero}()'

    if isinstance(value, str):
      value = ast.literal_eval(value)

    fbits = pyf.real_to_packedbits(float(value), fspec.exp, fspec.mant)

    return f'{dtype.nbits}\'b{fbits:0{dtype.nbits}b}'

  def _to_integer(self, value, dtype):
    if isinstance(value, Value):
      if isinstance(value.dtype, (Bool, Sint, Uint, Bits)):
        return f'int\'({self.svalue(value)})'
      elif isinstance(value.dtype, Float):
        fspec = self.float_spec(value.dtype)
        fpcall = self._get_fpcall('to_integer', NX=fspec.exp, NM=fspec.mant, NINT=32)
        return f'int\'({fpcall}({self.svalue(value)}))'
      elif isinstance(value.dtype, Real):
        return f'int\'({self.svalue(value)})'
      else:
        pyu.fatal(f'Unable to convert to integer: {value.dtype}')

    return str(value) if isinstance(value, int) else f'int\'({value})'

  def _to_real(self, value, dtype):
    if isinstance(value, Value):
      if isinstance(value.dtype, (Bool, Sint, Uint, Bits, Integer)):
        return f'real\'({self.svalue(value)})'
      elif isinstance(value.dtype, Float):
        fspec = self.float_spec(value.dtype)
        fpcall = self._get_fpcall('to_real', NX=fspec.exp, NM=fspec.mant)
        return f'{fpcall}({self.svalue(value)})'
      else:
        pyu.fatal(f'Unable to convert to real: {value.dtype}')

    return str(value) if isinstance(value, float) else f'real\'({value})'

  def _scalar_cast(self, value, dtype):
    if isinstance(dtype, Bool):
      return self._to_bool(value, dtype)
    if isinstance(dtype, Uint):
      return self._to_uint(value, dtype)
    if isinstance(dtype, Sint):
      return self._to_sint(value, dtype)
    if isinstance(dtype, Bits):
      return self._to_bits(value, dtype)
    if isinstance(dtype, Float):
      return self._to_float(value, dtype)
    if isinstance(dtype, Integer):
      return self._to_integer(value, dtype)
    if isinstance(dtype, Real):
      return self._to_real(value, dtype)

    pyu.fatal(f'Unknown type: {dtype}')

  def _do_cast(self, value, dtype):
    if not isinstance(value, Value):
      value = self._try_convert_literal(value)

    if isinstance(value, np.ndarray):
      shape = dtype.array_shape
      if shape != tuple(value.shape):
        pyu.fatal(f'Shape mismatch: {tuple(value.shape)} vs. {shape}')

      element_type = dtype.element_type()
      parts = []
      for idx in np.ndindex(shape):
        parts.append(self._scalar_cast(value[idx].item(), element_type))

      xvalue = flat2shape(parts, shape, '{', '}')
    elif isinstance(value, Value) and value.dtype.array_shape:
      shape, vshape = dtype.array_shape, value.dtype.array_shape
      if shape != vshape:
        pyu.fatal(f'Shape mismatch: {vshape} vs. {shape}')

      element_type = dtype.element_type()
      velement_type = value.dtype.element_type()
      avalue = paren(self.svalue(value))
      parts = []
      for idx in np.ndindex(shape):
        substr = ''.join(f'[{x}]' for x in idx)
        svalue = Value(velement_type, value=f'{avalue}{substr}')
        parts.append(self._scalar_cast(svalue, element_type))

      xvalue = flat2shape(parts, shape, '{', '}')
    else:
      xvalue = self._scalar_cast(unwrap(value), dtype)
      for size in reversed(dtype.array_shape):
        xvalue = f'\'{{{size}{{{xvalue}}}}}'

    return xvalue

  def _cast(self, value, dtype):
    if isinstance(value, Value) and value.dtype == dtype:
      return self.svalue(value)

    return self._do_cast(value, dtype)

  def cast(self, value, dtype, isreg=None):
    if isinstance(value, Value) and value.dtype == dtype:
      return value

    xvalue = self._do_cast(value, dtype)
    if isreg is None and isinstance(value, Value):
      isreg = value.isreg

    return Value(dtype, value=xvalue, isreg=isreg)

  def eval_tostring(self, value):
    xvalue = self.svalue(value)
    if isinstance(value, Value):
      if isinstance(value.dtype, (Uint, Sint, Integer)):
        return f'$sformatf("%d", {xvalue})'
      elif isinstance(value.dtype, (Bool, Bits)):
        return f'$sformatf("%b", {xvalue})'
      elif isinstance(value.dtype, Real):
        return f'$sformatf("%e", {xvalue})'
      elif isinstance(value.dtype, Float):
        fspec = self.float_spec(value.dtype)
        fpcall = self._get_fpcall('to_real', NX=fspec.exp, NM=fspec.mant)
        return f'$sformatf("%e", {fpcall}({xvalue}))'
      else:
        pyu.fatal(f'Unable to convert to real: {value.dtype}')

    return self.quote_string(xvalue)

  def quote_string(self, s):
    es = s.replace('"', '\\"')
    return f'"{es}"'

  def eval_token(self, token):
    if token == 'NOW':
      return '$sformatf("%t", $time)'

  def emit_finish(self):
    self.emit_code('$finish;')

  def emit_wait_for(self, t=None):
    if t is not None:
      self.emit_code(f'#{t}{self.time_unit()};')
    else:
      self.emit_code('forever;')

  def emit_wait_rising(self, *args):
    sargs = self.build_args_string(lambda a: f'posedge {paren(a)}', ' or ', args)
    self.emit_code(f'@({sargs});')

  def emit_wait_falling(self, *args):
    sargs = self.build_args_string(lambda a: f'negedge {paren(a)}', ' or ', args)
    self.emit_code(f'@({sargs});')

  def emit_wait_until(self, *args):
    sargs = self.build_args_string(lambda a: paren(a), ' or ', args)
    self.emit_code(f'@({sargs});')

  def emit_report(self, parts, severity=None):
    self.emit_write(parts)

  def emit_write(self, parts):
    self._emit_line('$display("' + ('%s' * len(parts)) + '", ' + ', '.join(parts) + ');')

  def _gen_array_access(self, arg, idx):
    idx = pyu.as_sequence(idx)

    ashape = arg.dtype.shape
    if len(idx) > len(ashape): pyu.fatal(f'Wrong indexing for shape: {idx} vs. {ashape}')

    shape, coords = [], []
    for i, ix in enumerate(idx):
      if isinstance(ix, slice):
        step = ix.step if ix.step is not None else 1

        if abs(step) != 1: pyu.fatal(f'Slice step must be 1: {step}')

        start, stop = pyu.norm_slice(ix.start, ix.stop, ashape[i])
        if start < 0 or start >= ashape[i] or stop < 0 or stop > ashape[i]:
          pyu.fatal(f'Slice index {i} of {arg} is out of bounds: {start} ... {stop} ({ashape[i]})')

        if step == 1:
          if i == len(ashape) - 1:
            coords.append(f'{stop - 1}: {start}')
          else:
            coords.append(f'{start}: {stop - 1}')
        else:
          if i == len(ashape) - 1:
            coords.append(f'{stop + 1}: {start}')
          else:
            coords.append(f'{start}: {stop + 1}')

        shape.append(abs(stop - start))
      else:
        if isinstance(ix, Value) and not isinstance(ix.dtype, Integer):
          ix = self._to_integer(ix, Integer())

        coords.append(self.svalue(ix))
        shape.append(1)

    shape = pyu.squeeze(shape + list(arg.dtype.full_shape[len(idx): ]), keep_dims=1,
                        sdir=pyu.MAJOR)
    avalue = self.svalue(arg) + ''.join(f'[{x}]' for x in coords)

    return avalue, shape

  def svalue(self, value):
    xvalue = value.value if isinstance(value, Value) else value

    if isinstance(xvalue, bool):
      xvalue = '1' if xvalue else '0'
    elif not isinstance(xvalue, str):
      xvalue = str(xvalue)

    return xvalue

  def flush(self):
    xlibs = tuple(sorted(self._extra_libs))

    return self._load_libs(extra_libs=xlibs) + self._expand()

  def is_root_variable(self, var):
    # Wires are always root!
    return var.isreg is False or (var.vspec is not None and var.vspec.const)

  def var_remap(self, var, is_store):
    # Do not remap anything which is not Value.
    # Do not remap registers (isreg == True), temporaries (isreg == None) or
    # not references.
    if not isinstance(var, Value) or var.isreg != False or var.ref is None:
      return var
    # Do not remap writes from the root process or simple reads.
    if self._proc.kind == ROOT_PROCESS or not is_store:
      return var

    wreg = self._wireregs.register(var)

    return wreg.reg

  def emit_declare_variable(self, name, var):
    if var.vspec is not None and var.vspec.const:
      vprefix, is_const = 'const ', True
    else:
      vprefix, is_const = '' if var.isreg else 'wire ', False

    vinit = ''
    if var.init is not None:
      if var.isreg or is_const:
        vinit = f' = {self._cast(var.init, var.dtype)}'
      else:
        wreg = self._wireregs.register(Wire(var.dtype, value=Ref(name, vspec=var.vspec)),
                                       init=var.init)

    ntype = self._type_of(var.dtype).format(name)

    self._emit_line(f'{vprefix}{ntype}{vinit};')

  def emit_assign(self, var, name, value):
    xvalue = self._cast(value, var.dtype)

    delay = self.get_context('delay')
    xdelay = f'#{paren(self.svalue(delay))} ' if delay is not None else ''

    cont_assign = 'assign ' if self._proc.kind == ROOT_PROCESS and not var.isreg else ''
    # Sequential designs (processes having posedge/negedge sensitivity) should use non
    # blocking assignments.
    asop = '=' if cont_assign or not self._edge_inputs else '<='

    self._emit_line(f'{xdelay}{cont_assign}{var.value} {asop} {xvalue};')

  def make_port_arg(self, port_arg):
    return port_arg

  def emit_entity(self, ent, kwargs, ent_name=None):
    if ent_name is None:
      ent_name = pyu.cname(ent)

    iname = self._get_entity_inst(ent_name)

    eparams, params = kwargs.pop(PARAM_KEY, None), ''
    if eparams:
      params = '#(' + ', '.join(f'.{k}({v})' for k, v in eparams.items()) + ') '

    with self.placement(self._entity_place):
      self._emit_line(f'{ent_name} {params}{iname}(')
      with self.indent():
        for i, pin in enumerate(ent.PORTS):
          arg = kwargs[pin.name]
          if not isinstance(arg, Value): pyu.fatal(f'Argument must be a Value subclass: {arg}')

          xarg = self.svalue(arg)
          port_bind = f'.{pin.name}({xarg})' + ('' if i == len(ent.PORTS) - 1 else ',')
          self._emit_line(port_bind)

      self._emit_line(f');')

  def emit_module_def(self, name, ent, comment=None):
    self._mod_comment = comment

  def emit_module_decl(self, name, ent):
    if self._mod_comment:
      self.emit_comment(self._mod_comment)

    self._emit_line(f'module {name}(' + ', '.join(ent.args.keys()) + ');')
    with self.indent():
      for name, ap in ent.args.items():
        pin, arg = ap.port, ap.arg
        if IO_NAME.get(pin.idir, None) is None: pyu.fatal(f'Invalid port direction: {pin.idir}')

        pdir = 'input' if pin.idir == IN else 'output' if pin.idir == OUT else 'inout'
        kind = 'reg' if pin.idir == OUT and arg.isreg else None
        ntype = self._type_of(arg.dtype, kind=kind).format(pin.name)

        self._emit_line(f'{pdir} {ntype};')

      self._init_module_places()

  def emit_module_end(self):
    with self.placement(self._module_vars_place):
      for wname, wreg in self._wireregs.reg_items():
        reg = wreg.reg
        vinit = f' = {self._cast(wreg.init, reg.dtype)}' if wreg.init is not None else ''
        ntype = self._type_of(reg.dtype).format(reg.value)
        self._emit_line(f'{ntype}{vinit};')

    with self.placement(self._modules_place):
      for iid, inst in self._itor:
        params = [f'.{k}({v})' for k, v in inst.params.items()]
        args = [f'.{k}({self.svalue(v)})' for k, v in inst.args.items()]

        self._emit_line(f'{inst.name} #(' + ', '.join(params) + f') {iid}(' + ', '.join(args) + ');')

    with self.indent():
      for wname, wreg in self._wireregs.reg_items():
        reg = wreg.reg
        self._emit_line(f'assign {wreg.wire.value} = {wreg.reg.value};')

    self._emit_line(f'endmodule')
    self._module_reset()

  def emit_process_decl(self, name, sensitivity=None, process_kind=None,
                        process_args=None):
    self._process_init(name, process_kind, process_args, sensitivity)

    if process_kind == INIT_PROCESS:
      if sensitivity: pyu.fatal(f'Sensitivity list not allowed in init process')
      self._emit_line('initial')
    elif sensitivity:
      conds = []
      for sname, sens in sensitivity.items():
        if sens.trigger == POSEDGE:
          conds.append(f'posedge {paren(sname)}')
          self._edge_inputs.append((sname, sens))
        elif sens.trigger == NEGEDGE:
          conds.append(f'negedge {paren(sname)}')
          self._edge_inputs.append((sname, sens))
        else:
          conds.append(paren(sname))

      self._emit_line(f'always @(' + ' or '.join(conds) + ')')
    else:
      self._emit_line('always')

  def emit_process_begin(self):
    if self._proc.name:
      self._emit_line(f'{self._proc.name} : begin')
    else:
      self._emit_line(f'begin')
    self._process_vars_place = self.emit_placement(extra_indent=1)

  def _process_reset(self):
    super()._process_reset()
    self._edge_inputs = []

  def emit_process_end(self):
    self._emit_line(f'end')
    self._process_reset()

  def emit_comment(self, msg):
    for ln in msg.split('\n'):
      self._emit_line(f'// {ln}')

  def emit_If(self, test):
    xtest = self._cast(test, BOOL)
    self._emit_line(f'if {paren(xtest)} begin')

  def emit_Elif(self, test):
    xtest = self._cast(test, BOOL)
    self._emit_line(f'end else if {paren(xtest)} begin')

  def emit_Else(self):
    self._emit_line(f'end else begin')

  def emit_EndIf(self):
    self._emit_line(f'end')

  def emit_Assert(self, test, parts):
    xtest = self.svalue(test)
    if parts:
      self._emit_line(f'assert {xtest} else $error("' + ('%s' * len(parts)) + '", ' + ', '.join(parts) + '");')
    else:
      self._emit_line(f'assert {xtest};')

  def emit_match_cases(self, subject, cases):
    xsubject = self.svalue(subject)
    self._emit_line(f'case ({xsubject})')

    with self.indent():
      for mc in cases:
        sblock = ' begin' if len(mc.scope) > 1 else ''
        if mc.pattern is not None:
          xpattern = self._cast(mc.pattern, subject.dtype)
          self._emit_line(f'{paren(xpattern)}:{sblock}')
        else:
          self._emit_line(f'default:{sblock}')

        if sblock:
          with self.indent():
            self._emit(mc.scope)
          self._emit_line(f'end')
        else:
          self._emit(mc.scope)

    self._emit_line(f'endcase')

  def _build_op(self, op, left, right):
    sop = _OPSYMS[pyu.classof(op)]
    if sop.isfn:
      return f'{sop.sym}({paren(left)}, {paren(right)})'
    else:
      return f'{paren(left)} {sop.sym} {paren(right)}'

  def _build_arith_op(self, op, left, right, dtype):
    if isinstance(dtype, Float):
      fspec = self.float_spec(dtype)
      opfn = _FLOAT_OPFNS[pyu.classof(op)]
      fpcall = self._get_fpcall(opfn, NX=fspec.exp, NM=fspec.mant)
      return f'{fpcall}({left}, {right})'
    else:
      return self._build_op(op, left, right)

  def eval_BinOp(self, op, left, right):
    if isinstance(op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod)):
      left, right = self._marshal_arith_op([left, right],
                                           ctype_nocast=_ARITH_CTYPE_NOCAST)
      xleft, xright = self.svalue(left), self.svalue(right)

      pyu.mlog(lambda: f'\tBinOp: {xleft}\t{pyu.cname(op)}\t{xright}')
      result = self._build_arith_op(op, xleft, xright, left.dtype)
      # The signed/unsigned multiplication result has a number of bits which is the
      # sum of the ones of the operands, which is not the behaviour we want.
      if isinstance(op, ast.Mult) and isinstance(left.dtype, (Sint, Uint)):
        result = f'{left.dtype.nbits}\'({result})'

      return Value(left.dtype, value=result)
    elif isinstance(op, (ast.LShift, ast.RShift)):
      left, right = self._marshal_shift_op(left, right)
      xleft, xright = self.svalue(left), self.svalue(right)

      pyu.mlog(lambda: f'\tBinOp: {xleft}\t{pyu.cname(op)}\t{xright}')

      return Value(left.dtype, value=self._build_op(op, xleft, xright))
    elif isinstance(op, (ast.BitOr, ast.BitXor, ast.BitAnd)):
      left, right = self._marshal_bit_op([left, right])
      xleft, xright = self.svalue(left), self.svalue(right)

      pyu.mlog(lambda: f'\tBinOp: {xleft}\t{pyu.cname(op)}\t{xright}')

      return Value(left.dtype, value=self._build_op(op, xleft, xright))
    elif isinstance(op, ast.MatMult):
      # Steal MatMult ('@') for concatenation!
      dtype, (left, right) = self._marshal_concat_op([left, right])
      xleft, xright = self.svalue(left), self.svalue(right)

      pyu.mlog(lambda: f'\tBinOp: {xleft}\t{pyu.cname(op)}\t{xright}')

      return Value(dtype, value=f'{{{xleft}, {xright}}}')
    else:
      pyu.fatal(f'Unsupported operation: {op}')

  def eval_UnaryOp(self, op, arg):
    xvalue = self.svalue(arg)

    pyu.mlog(lambda: f'\tUnaryOp: {pyu.cname(op)}\t{xvalue}')

    if isinstance(op, ast.UAdd):
      # Unary addition is a noop for HDL data types.
      result = xvalue
    else:
      if isinstance(arg, Value) and isinstance(arg.dtype, Float):
        if isinstance(op, ast.USub):
          fspec = self.float_spec(arg.dtype)
          fpcall = self._get_fpcall('neg', NX=fspec.exp, NM=fspec.mant)
          result = f'{fpcall}({xvalue})'
        else:
          pyu.fatal(f'Unsupported operation for type {arg.dtype}: {op}')
      else:
        if isinstance(op, ast.USub):
          result = f'-{paren(xvalue)}'
        elif isinstance(op, ast.Not):
          result = f'!{paren(xvalue)}'
        elif isinstance(op, ast.Invert):
          result = f'~{paren(xvalue)}'
        else:
          pyu.fatal(f'Unsupported operation for type {arg.dtype}: {op}')

    return Value(arg.dtype, value=result)

  def eval_BoolOp(self, op, args):
    xargs = [self._cast(a, BOOL) for a in args]

    pyu.mlog(lambda: f'\tBoolOp: {pyu.cname(op)}\t{pyu.stri(xargs)}')

    if isinstance(op, ast.And):
      result = self._paren_join(' && ', xargs)
    elif isinstance(op, ast.Or):
      result = self._paren_join(' || ', xargs)
    else:
      pyu.fatal(f'Unsupported operation: {op}')

    return Value(BOOL, value=result)

  def eval_Compare(self, left, ops, comps):
    comps = self._marshal_compare_op([left] + list(comps))
    xcomps = [self.svalue(comp) for comp in comps]

    pyu.mlog(lambda: f'\tCompare: {[pyu.cname(x) for x in ops]}\t{pyu.stri(xcomps)}')

    results = []
    for i, op in enumerate(ops):
      cres = self._build_op(op, xcomps[i], xcomps[i + 1])
      results.append(cres)

    result = self._paren_join(' && ', results)

    return Value(BOOL, value=result)

  def eval_Subscript(self, arg, idx):
    result, shape = self._gen_array_access(arg, idx)

    return arg.new_value(result, shape=shape)

  def eval_IfExp(self, test, body, orelse):
    xtest = self.svalue(test)
    body, orelse = self._marshal_ifexp_op([body, orelse])
    xbody, xorelse = self.svalue(body), self.svalue(orelse)

    pyu.mlog(lambda: f'\tIfExp: {xtest} ? {xbody} : {xorelse}')

    return Value(body.dtype, f'{paren(xtest)} ? {xbody} : {xorelse}')


# Register Verilog emitter class.
Emitter.register(VERILOG, Verilog_Emitter)

