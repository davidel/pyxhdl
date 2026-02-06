import ast
import collections
import functools
import inspect
import os
import re

import numpy as np

import py_misc_utils.alog as alog
import py_misc_utils.core_utils as pycu
import py_misc_utils.fp_utils as pyf
import py_misc_utils.inspect_utils as pyiu
import py_misc_utils.utils as pyu

from .entity import *
from .emitter import *
from .instantiator import *
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
  'is_nan': _SVMod('fpu', 'is_nan'),
  'is_inf': _SVMod('fpu', 'is_inf'),
  'is_zero': _SVMod('fpu', 'is_zero'),
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


class Verilog_Emitter(Emitter):

  def __init__(self, cfg_file=None, **kwargs):
    super().__init__(cfg_file=cfg_file, **kwargs)
    self.kind = 'verilog'
    self.file_ext = '.sv'
    self.eol = ';'
    self._mod_comment = None
    self._init_module_places()
    self._module_reset()
    self._extra_libs = set()

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
    margs = pycu.new_with(kwargs, **{exp_param: fspec.exp, mant_param: fspec.mant})
    iid = self._iface_id(mod_name, **margs)

    return f'{iid}.{fnname}'

  def _init_module_places(self):
    self.module_vars_place = self.emit_placement()
    self._modules_place = self.emit_placement()
    self._entity_place = self.emit_placement()

  def _module_reset(self):
    self._mod_comment = None
    self._itor = Instanciator(param_key=PARAM_KEY)

    self._process_reset()

  def _iface_id(self, mod_name, **kwargs):
    self._extra_libs.add(mod_name)

    # This API instantiates only Verilog interfaces, which takes no arguments
    # (only parameters).
    return self._itor.getid(mod_name, {PARAM_KEY: kwargs})

  def _get_fpcall(self, fnname, **kwargs):
    fn_map = pyu.dict_rget(self._cfg, 'verilog/fpu_fnmap', defval=_FPU_FNMAP)
    svmod = fn_map.get(fnname)
    if svmod is None:
      fatal(f'Unable to find configuration for FPU function: {fnname}')

    iid = self._iface_id(svmod.mod, **kwargs)

    return f'{iid}.{svmod.fnname}'

  def _scalar_remap(self, value):
    if isinstance(value, bool):
      return '1' if value else '0'

  def _type_of(self, dtype):
    kind = 'logic'
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

    fatal(f'Unknown type: {dtype}', exc=TypeError)

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
        fatal(f'Unknown type: {value.dtype}', exc=TypeError)

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
      return Value(BOOL, '1' if value else '0')
    if value is None:
      return Value(VOID)
    if isinstance(value, str):
      bvalue = bitstring(value, remap=lambda x: _LOGIC_REMAP[x])
      if bvalue is not None:
        return bvalue.new_value(f'{bvalue.dtype.nbits}\'b{bvalue.value}')

      dtype, ivalue = self._match_intstring(value)
      if dtype is not None:
        if isinstance(dtype, Uint):
          return Value(dtype, f'{dtype.nbits}\'({ivalue})')
        else:
          return Value(dtype, f'signed\'({dtype.nbits}\'({ivalue}))')

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
      if value.dtype == dtype:
        return self.svalue(value)
      elif isinstance(value.dtype, (Bool, Sint, Uint, Bits)):
        return f'int\'({self.svalue(value)})'
      elif isinstance(value.dtype, Float):
        fspec = self.float_spec(value.dtype)
        fpcall = self._get_fpcall('to_integer', NX=fspec.exp, NM=fspec.mant, NINT=32)
        return f'int\'({fpcall}({self.svalue(value)}))'
      elif isinstance(value.dtype, Real):
        return f'int\'({self.svalue(value)})'
      else:
        fatal(f'Unable to convert to integer: {value} {dtype}')

    return str(value) if isinstance(value, int) else f'int\'({value})'

  def _to_real(self, value, dtype):
    if isinstance(value, Value):
      if value.dtype == dtype:
        return self.svalue(value)
      elif isinstance(value.dtype, (Bool, Sint, Uint, Bits, Integer)):
        return f'real\'({self.svalue(value)})'
      elif isinstance(value.dtype, Float):
        fspec = self.float_spec(value.dtype)
        fpcall = self._get_fpcall('to_real', NX=fspec.exp, NM=fspec.mant)
        return f'{fpcall}({self.svalue(value)})'
      else:
        fatal(f'Unable to convert to real: {value} {dtype}')

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

    fatal(f'Unknown type: {dtype}')

  def _do_cast(self, value, dtype):
    if not isinstance(value, Value):
      value = self._try_convert_literal(value)

    if isinstance(value, np.ndarray):
      shape = dtype.array_shape
      if shape != tuple(value.shape):
        fatal(f'Shape mismatch: {tuple(value.shape)} vs. {shape}')

      element_type = dtype.element_type()
      parts = []
      for idx in np.ndindex(shape):
        parts.append(self._scalar_cast(value[idx].item(), element_type))

      xvalue = flat2shape(parts, shape, '{', '}')
    elif isinstance(value, Value) and value.dtype.array_shape:
      shape, vshape = dtype.array_shape, value.dtype.array_shape
      if shape != vshape:
        fatal(f'Shape mismatch: {vshape} vs. {shape}')

      element_type = dtype.element_type()
      velement_type = value.dtype.element_type()
      avalue = paren(self.svalue(value))
      parts = []
      for idx in np.ndindex(shape):
        substr = ''.join(f'[{x}]' for x in idx)
        svalue = Value(velement_type, f'{avalue}{substr}')
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

    return Value(dtype, xvalue, isreg=isreg)

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
        fatal(f'Unable to convert to string: {value}')

    return self.quote_string(xvalue)

  def quote_string(self, s):
    es = s.replace('"', '\\"')
    return f'"{es}"'

  def eval_token(self, token):
    if token == 'NOW':
      time_fmt = os.getenv('TIME_FMT', '%0t')
      return f'$sformatf("{time_fmt}", $time)'

  def emit_finish(self):
    self.emit_code('$finish;')

  def emit_wait_for(self, ts=None):
    if ts is not None:
      wts, tu = self._normalize_time(ts)
      self.emit_code(f'#{wts}{tu};')
    else:
      self.emit_code('forever;')

  def emit_wait_rising(self, arg):
    self.emit_code(f'@(posedge {paren(self.svalue(arg))});')

  def emit_wait_falling(self, arg):
    self.emit_code(f'@(negedge {paren(self.svalue(arg))});')

  def emit_wait_until(self, arg):
    self.emit_code(f'@({paren(self.svalue(arg))});')

  def emit_report(self, parts, severity=None):
    self.emit_write(parts)

  def emit_write(self, parts):
    self._emit_line('$display("' + ('%s' * len(parts)) + '", ' + ', '.join(parts) + ');')

  def _gen_array_access(self, arg, idx):
    idx = pyu.as_sequence(idx)

    ashape = arg.dtype.shape
    if len(idx) > len(ashape):
      fatal(f'Wrong indexing for shape: {idx} vs. {ashape}')

    shape, coords = [], []
    for i, ix in enumerate(idx):
      if isinstance(ix, slice):
        if isinstance(ix.start, Value):
          if ix.stop is not None:
            fatal(f'Variable part select ({arg} [{i}]) slice stop must be empty: {ix.stop}')
          if ix.step > ashape[i]:
            fatal(f'Variable part select ({arg} [{i}]) is too big: {ix.step} ({ashape[i]})')

          base = self._to_integer(ix.start, Integer())

          if i == len(ashape) - 1:
            coords.append(f'{paren(base)} -: {ix.step}')
          else:
            coords.append(f'{paren(base)} +: {ix.step}')

          shape.append(ix.step)
        else:
          step = ix.step if ix.step is not None else 1

          if abs(step) != 1:
            fatal(f'Slice step must be 1: {step}')

          start, stop = pycu.norm_slice(ix.start, ix.stop, ashape[i])
          if start < 0 or start >= ashape[i] or stop < 0 or stop > ashape[i]:
            fatal(f'Slice ({arg} [{i}]) is out of bounds: {start} ... {stop} ({ashape[i]})')

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
    avalue = paren(self.svalue(arg), kind='{}') + ''.join(f'[{x}]' for x in coords)

    return avalue, shape

  def flush(self):
    xlibs = tuple(sorted(self._extra_libs))

    return self._load_libs(extra_libs=xlibs) + self._expand()

  def is_root_variable(self, var):
    return var.isreg or var.is_const()

  def var_remap(self, var, is_store):
    return var

  def _emit_attributes(self, attributes):
    attrs = []
    for aname, avalue in self._enum_attributes(attributes):
      if isinstance(avalue, str):
        attrs.append(f'{aname} = "{avalue}"')
      else:
        attrs.append(f'{aname} = {avalue}')

    if attrs:
      self._emit_line('(* ' + ', '.join(attrs) + ' *)')

  def emit_declare_variable(self, name, var):
    if var.is_const():
      vprefix, is_const = 'const ', True
    else:
      vprefix, is_const = '', False

    vinit = ''
    if var.init is not None:
      vinit = f' = {self._cast(var.init, var.dtype)}'
      if not self.is_root_variable(var) and self._proc.kind != ROOT_PROCESS:
        vprefix = f'static {vprefix}'

    ntype = self._type_of(var.dtype).format(name)

    vspec = var.vspec
    if vspec is not None and vspec.attributes is not None:
      self._emit_attributes(vspec.attributes)

    self._emit_line(f'{vprefix}{ntype}{vinit};')

  def emit_assign(self, var, name, value):
    xvalue = self._cast(value, var.dtype)

    delay = self.get_context('delay')
    xdelay = f'#{paren(self.svalue(delay))} ' if delay is not None else ''

    cont_assign = 'assign ' if self._proc.kind == ROOT_PROCESS else ''
    # Sequential designs (processes having posedge/negedge sensitivity) should use non
    # blocking assignments.
    asop = '=' if cont_assign or not self._edge_inputs or not var.isreg else '<='

    self._emit_line(f'{xdelay}{cont_assign}{var.value} {asop} {xvalue};')

  def make_port_arg(self, port_arg):
    return port_arg

  def emit_entity(self, ent, kwargs, ent_name=None):
    if ent_name is None:
      ent_name = pyiu.cname(ent)

    iname = self._get_entity_inst(ent_name)

    eparams, params = kwargs.pop(PARAM_KEY, None), ''
    if eparams:
      params = '#(' + ', '.join(f'.{k}({v})' for k, v in eparams.items()) + ') '

    with self.placement(self._entity_place):
      self._emit_line(f'{ent_name} {params}{iname}(')
      with self.indent():
        binds = []
        for i, pin in enumerate(ent.PORTS):
          arg = kwargs[pin.name]

          if pin.is_ifc():
            xargs = pin.ifc_expand(arg)
          else:
            xargs = ((pin, arg),)

          for xpin, xarg in xargs:
            if not isinstance(xarg, Value):
              fatal(f'Argument must be a Value subclass: {xarg}')

            if xarg.is_none():
              binds.append(f'.{xpin.name}()')
            else:
              earg = self.svalue(xarg)
              binds.append(f'.{xpin.name}({earg})')

        for i, port_bind in enumerate(binds):
          self._emit_line(port_bind + ('' if i == len(binds) - 1 else ','))

      self._emit_line(f');')

  def emit_module_def(self, name, ent, comment=None):
    self._mod_comment = comment

  def emit_module_decl(self, name, ent):
    if self._mod_comment:
      self.emit_comment(self._mod_comment)

    xports = ent.expanded_ports()

    self._emit_line(f'module {name}(' + ', '.join(ap.port.name for ap in xports) + ');')
    with self.indent():
      for ap in xports:
        pin, arg = ap.port, ap.arg

        pdir = 'input' if pin.is_ro() else 'output' if pin.is_wo() else 'inout'
        ntype = self._type_of(arg.dtype).format(pin.name)

        self._emit_line(f'{pdir} {ntype};')

      self._init_module_places()

  def emit_module_end(self):
    with self.placement(self._modules_place):
      for iid, inst in self._itor:
        params = [f'.{k}({v})' for k, v in inst.params.items()]
        args = [f'.{k}({self.svalue(v)})' for k, v in inst.args.items()]

        self._emit_line(f'{inst.name} #(' + ', '.join(params) + f') {iid}(' + ', '.join(args) + ');')

    self._emit_line(f'endmodule')
    self._module_reset()

  def emit_process_decl(self, name, sensitivity=None, process_kind=None,
                        process_args=None):
    self._process_init(name, process_kind, process_args, sensitivity)

    if process_kind == INIT_PROCESS:
      if sensitivity:
        fatal(f'Sensitivity list not allowed in init process')

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

      if len(conds) > len(self._edge_inputs):
        self._emit_line(f'always @(' + ' or '.join(conds) + ')')
      else:
        self._emit_line(f'always_ff @(' + ' or '.join(conds) + ')')
    else:
      proc_mode = process_args.get('proc_mode') if process_args else None
      if proc_mode == 'comb':
        self._emit_line('always_comb')
      elif proc_mode == 'latch':
        self._emit_line('always_latch')
      elif proc_mode == 'loop':
        self._emit_line('always')
      else:
        self._emit_line('always @(*)')

  def emit_process_begin(self):
    if self._proc.name:
      self._emit_line(f'{self._proc.name} : begin')
    else:
      self._emit_line(f'begin')
    self.process_vars_place = self.emit_placement(extra_indent=1)

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
        if mc.pattern is not None:
          xpattern = self._cast(mc.pattern, subject.dtype)
          self._emit_line(f'{paren(xpattern)}: begin')
        else:
          self._emit_line(f'default: begin')

        with self.indent():
          self._emit(mc.scope)
        self._emit_line(f'end')

    self._emit_line(f'endcase')

  def _build_op(self, op, left, right):
    sop = _OPSYMS[pyiu.classof(op)]
    if sop.isfn:
      return f'{sop.sym}({paren(left)}, {paren(right)})'
    else:
      return f'{paren(left)} {sop.sym} {paren(right)}'

  def _build_arith_op(self, op, left, right, dtype):
    if isinstance(dtype, Float):
      fspec = self.float_spec(dtype)
      opfn = _FLOAT_OPFNS[pyiu.classof(op)]
      fpcall = self._get_fpcall(opfn, NX=fspec.exp, NM=fspec.mant)
      return f'{fpcall}({left}, {right})'
    else:
      return self._build_op(op, left, right)

  def eval_BinOp(self, op, left, right):
    if isinstance(op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod)):
      left, right = self._marshal_arith_op([left, right],
                                           ctype_nocast=_ARITH_CTYPE_NOCAST)
      xleft, xright = self.svalue(left), self.svalue(right)

      alog.debug(lambda: f'\tBinOp: {xleft}\t{pyiu.cname(op)}\t{xright}')
      result = self._build_arith_op(op, xleft, xright, left.dtype)
      # The signed/unsigned multiplication result has a number of bits which is the
      # sum of the ones of the operands, which is not the behaviour we want.
      if isinstance(op, ast.Mult) and isinstance(left.dtype, (Sint, Uint)):
        result = f'{left.dtype.nbits}\'({result})'

      return Value(left.dtype, result)
    elif isinstance(op, (ast.LShift, ast.RShift)):
      left, right = self._marshal_shift_op(left, right)
      xleft, xright = self.svalue(left), self.svalue(right)

      alog.debug(lambda: f'\tBinOp: {xleft}\t{pyiu.cname(op)}\t{xright}')

      return Value(left.dtype, self._build_op(op, xleft, xright))
    elif isinstance(op, (ast.BitOr, ast.BitXor, ast.BitAnd)):
      left, right = self._marshal_bit_op([left, right])
      xleft, xright = self.svalue(left), self.svalue(right)

      alog.debug(lambda: f'\tBinOp: {xleft}\t{pyiu.cname(op)}\t{xright}')

      return Value(left.dtype, self._build_op(op, xleft, xright))
    elif isinstance(op, ast.MatMult):
      # Steal MatMult ('@') for concatenation!
      dtype, (left, right) = self._marshal_concat_op([left, right])
      xleft, xright = self.svalue(left), self.svalue(right)

      alog.debug(lambda: f'\tBinOp: {xleft}\t{pyiu.cname(op)}\t{xright}')

      return Value(dtype, f'{{{xleft}, {xright}}}')
    else:
      fatal(f'Unsupported operation: {op}')

  def eval_UnaryOp(self, op, arg):
    xvalue = self.svalue(arg)

    alog.debug(lambda: f'\tUnaryOp: {pyiu.cname(op)}\t{xvalue}')

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
          fatal(f'Unsupported operation for type {arg.dtype}: {op}')
      else:
        if isinstance(op, ast.USub):
          result = f'-{paren(xvalue)}'
        elif isinstance(op, ast.Not):
          result = f'!{paren(xvalue)}'
        elif isinstance(op, ast.Invert):
          result = f'~{paren(xvalue)}'
        else:
          fatal(f'Unsupported operation for type {arg.dtype}: {op}')

    return Value(arg.dtype, result)

  def eval_BoolOp(self, op, args):
    xargs = [self._cast(a, BOOL) for a in args]

    alog.debug(lambda: f'\tBoolOp: {pyiu.cname(op)}\t{pyu.stri(xargs)}')

    if isinstance(op, ast.And):
      result = self._paren_join(' && ', xargs)
    elif isinstance(op, ast.Or):
      result = self._paren_join(' || ', xargs)
    else:
      fatal(f'Unsupported operation: {op}')

    return Value(BOOL, result)

  def eval_Compare(self, left, ops, comps):
    comps = self._marshal_compare_op([left] + list(comps))
    xcomps = [self.svalue(comp) for comp in comps]

    alog.debug(lambda: f'\tCompare: {[pyiu.cname(x) for x in ops]}\t{pyu.stri(xcomps)}')

    results = []
    for i, op in enumerate(ops):
      cres = self._build_op(op, xcomps[i], xcomps[i + 1])
      results.append(cres)

    result = self._paren_join(' && ', results)

    return Value(BOOL, result)

  def eval_Subscript(self, arg, idx):
    result, shape = self._gen_array_access(arg, idx)

    return arg.new_value(result, shape=shape, keepref=True)

  def eval_IfExp(self, test, body, orelse):
    xtest = self.svalue(test)
    body, orelse = self._marshal_ifexp_op([body, orelse])
    xbody, xorelse = self.svalue(body), self.svalue(orelse)

    alog.debug(lambda: f'\tIfExp: {xtest} ? {xbody} : {xorelse}')

    return Value(body.dtype, f'{paren(xtest)} ? {xbody} : {xorelse}')

  # Extension functions.
  def eval_is_nan(self, value):
    if not isinstance(value.dtype, Float):
      fatal(f'Unsupported type: {value.dtype}')

    fspec = self.float_spec(value.dtype)
    fpcall = self._get_fpcall('is_nan', NX=fspec.exp, NM=fspec.mant)
    result = f'{fpcall}({self.svalue(value)})'

    return Value(BOOL, result)

  def eval_is_inf(self, value):
    if not isinstance(value.dtype, Float):
      fatal(f'Unsupported type: {value.dtype}')

    fspec = self.float_spec(value.dtype)
    fpcall = self._get_fpcall('is_inf', NX=fspec.exp, NM=fspec.mant)
    result = f'{fpcall}({self.svalue(value)})'

    return Value(BOOL, result)


# Register Verilog (SystemVerilog >= 2012) emitter class.
Emitter.register('verilog', Verilog_Emitter)

