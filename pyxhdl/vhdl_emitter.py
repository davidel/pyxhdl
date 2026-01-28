import ast
import collections
import functools
import inspect
import os
import re

import numpy as np

import py_misc_utils.core_utils as pycu
import py_misc_utils.inspect_utils as pyiu
import py_misc_utils.utils as pyu

from .entity import *
from .emitter import *
from .pyxhdl import *
from .types import *
from .utils import *
from .vars import *
from .wrap import *


_STD_HEADER = """library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;
use ieee.float_pkg.all;
use std.textio.all;

library work;
use work.all;
"""

# Describe which Python types can be fed directly to VHDL operators on the
# types in the dictionary values set.
_ARITH_CTYPE_NOCAST = {
  int: {Uint, Sint, Float, Real, Integer},
  float: {Float, Real},
}

_OPSYMS = {
  ast.Add: OpSym('+'),
  ast.Sub: OpSym('-'),
  ast.Mult: OpSym('*'),
  ast.Div: OpSym('/'),
  ast.Mod: OpSym('mod'),
  ast.BitOr: OpSym('or'),
  ast.BitXor: OpSym('xor'),
  ast.BitAnd: OpSym('and'),
  ast.MatMult: OpSym('&'),
  ast.Eq: OpSym('='),
  ast.NotEq: OpSym('/='),
  ast.Lt: OpSym('<'),
  ast.LtE: OpSym('<='),
  ast.Gt: OpSym('>'),
  ast.GtE: OpSym('>='),
  ast.LShift: OpSym('pyxhdl.bit_shl', True),
  ast.RShift: OpSym('pyxhdl.bit_shr', True),
}


class VHDL_Emitter(Emitter):

  def __init__(self, cfg_file=None, **kwargs):
    super().__init__(cfg_file=cfg_file, **kwargs)
    self.kind = 'vhdl'
    self.file_ext = '.vhd'
    self.eol = ';'
    self._arch = self._cfg.get('entity_arch', 'behavior')
    self._mod_comment = None
    self._proc_indent = 0
    self.module_vars_place = self.emit_placement()
    self._entity_place = self.emit_placement()

  def _emit_header(self):
    hdr = self._cfg.get('header', _STD_HEADER)
    for ln in hdr.split('\n'):
      self._emit_line(ln)

  def _scalar_remap(self, value):
    if isinstance(value, bool):
      return 'true' if value else 'false'

  def _type_of(self, dtype):
    nbits, shape = dtype.nbits, dtype.array_shape

    adims = ''.join(f'(0 to {x - 1})' for x in shape)
    if isinstance(dtype, Uint):
      if shape:
        return f'pyxhdl.uint_array{len(shape)}d{adims}({nbits - 1} downto 0)'
      else:
        return f'unsigned({nbits - 1} downto 0)'
    elif isinstance(dtype, Sint):
      if shape:
        return f'pyxhdl.sint_array{len(shape)}d{adims}({nbits - 1} downto 0)'
      else:
        return f'signed({nbits - 1} downto 0)'
    elif isinstance(dtype, Bits):
      if nbits == 1:
        return f'pyxhdl.slv_array{len(shape)}d{adims}' if shape else 'std_logic'

      if shape:
        return f'pyxhdl.bits_array{len(shape)}d{adims}({nbits - 1} downto 0)'
      else:
        return f'std_logic_vector({nbits - 1} downto 0)'
    elif isinstance(dtype, Bool):
      return f'pyxhdl.bool_array{len(shape)}d{adims}' if shape else 'boolean'
    elif isinstance(dtype, Integer):
      return f'pyxhdl.integer_array{len(shape)}d{adims}' if shape else 'integer'
    elif isinstance(dtype, Real):
      return f'pyxhdl.real_array{len(shape)}d{adims}' if shape else 'real'
    elif isinstance(dtype, Float):
      fspec = self.float_spec(dtype)
      if shape:
        return f'pyxhdl.float_array{len(shape)}d{adims}({fspec.exp} downto {-fspec.mant})'
      else:
        return f'float({fspec.exp} downto {-fspec.mant})'

    pyu.fatal(f'Unknown type: {dtype}', exc=TypeError)

  def _resize_bits(self, value, nbits):
    if value.dtype.nbits == nbits:
      return value

    xvalue = self.svalue(value)
    result = f'pyxhdl.bits_resize({xvalue}, {nbits})'

    shape = list(value.dtype.shape)
    shape[-1] = nbits

    return value.new_value(result, shape=shape)

  def _to_bool(self, value, dtype):
    if isinstance(value, Value):
      xvalue = self.svalue(value)
      if (isinstance(value.dtype, (Sint, Uint)) or
          (isinstance(value.dtype, Bits) and value.dtype.nbits > 1)):
        return f'and({xvalue})'

      zero = self._cast(0, value.dtype)
      return f'{paren(xvalue)} /= {zero}'

    if isinstance(value, str):
      value = ast.literal_eval(value)

    return 'true' if value else 'false'

  def _to_int(self, value, dtype, itype):
    if isinstance(value, Value):
      if isinstance(value.dtype, (Uint, Sint)):
        xvalue = self.svalue(value)
        rsvalue = f'resize({xvalue}, {dtype.nbits})' if value.dtype.nbits != dtype.nbits else xvalue
        return f'{itype}({rsvalue})' if type(dtype) != type(value.dtype) else rsvalue
      elif isinstance(value.dtype, Bits):
        xvalue = self.svalue(value)
        return f'pyxhdl.cvt_{itype}({xvalue}, {dtype.nbits})'
      elif isinstance(value.dtype, Integer):
        return f'to_{itype}({self.svalue(value)}, {dtype.nbits})'
      elif isinstance(value.dtype, Real):
        return f'to_{itype}(integer({self.svalue(value)}), {dtype.nbits})'
      elif isinstance(value.dtype, Bool):
        zero = f'to_{itype}(0, {dtype.nbits})'
        one = f'to_{itype}(1, {dtype.nbits})'
        xvalue = self.svalue(value)
        return f'pyxhdl.{dtype.name}_ifexp({xvalue}, {one}, {zero})'

    xvalue = self.svalue(value)
    return f'to_{itype}({xvalue}, {dtype.nbits})'

  def _to_uint(self, value, dtype):
    return self._to_int(value, dtype, 'unsigned')

  def _to_sint(self, value, dtype):
    return self._to_int(value, dtype, 'signed')

  def _try_convert_literal(self, value):
    # This API should not try to convert Python `int` or `float` literals, as those
    # are better off directly going to the cast operators, resulting in less bits
    # resize operations.
    if value is True or value is False:
      return Value(BOOL, 'true' if value else 'false')
    if value is None:
      return Value(VOID)
    if isinstance(value, str):
      bvalue = bitstring(value)
      if bvalue is not None:
        return bvalue.new_value(f'"{bvalue.value}"' if bvalue.dtype.nbits > 1
                                else f'\'{bvalue.value}\'')

      dtype, ivalue = self._match_intstring(value)
      if dtype is not None:
        if isinstance(dtype, Uint):
          return Value(dtype, f'to_unsigned({ivalue}, {dtype.nbits})')
        else:
          return Value(dtype, f'to_signed({ivalue}, {dtype.nbits})')

    return value

  def _to_bits(self, value, dtype):
    if isinstance(value, Value):
      if isinstance(value.dtype, (Uint, Sint)):
        xvalue = self.svalue(value)
        if value.dtype.nbits != dtype.nbits:
          xvalue = f'resize({xvalue}, {dtype.nbits})'
        return f'std_logic_vector({xvalue})' if dtype.nbits > 1 else xvalue
      elif isinstance(value.dtype, Bits):
        value = self._resize_bits(value, dtype.nbits)
        return self.svalue(value)
      elif isinstance(value.dtype, Integer):
        return f'std_logic_vector(to_unsigned({self.svalue(value)}, {dtype.nbits}))'
      elif isinstance(value.dtype, Real):
        return f'std_logic_vector(to_unsigned(integer({self.svalue(value)}), {dtype.nbits}))'
      elif isinstance(value.dtype, Bool):
        xvalue = self.svalue(value)
        result = f'pyxhdl.{dtype.name}_ifexp({xvalue}, \'1\', \'0\')'
        if dtype.nbits > 1:
          result = '"' + ('0' * (dtype.nbits - 1)) + '" & ' + result

        return result

    if dtype.nbits == 1:
      return f'\'{value[-1]}\'' if isinstance(value, str) else f'\'{value}\''

    if isinstance(value, str):
      if value.startswith('0b'):
        value = value[2: ]
      if dtype.nbits > len(value):
        bvalue = ('0' * (dtype.nbits - len(value))) + value
      else:
        bvalue = value[-dtype.nbits: ]

      return f'"{bvalue.upper()}"'

    return f'std_logic_vector(to_unsigned({value}, {dtype.nbits}))'

  def _to_float(self, value, dtype):
    fspec = self.float_spec(dtype)
    xvalue = self.svalue(value)
    if isinstance(value, Value):
      if isinstance(value.dtype, Float):
        return f'resize({xvalue}, {fspec.exp}, {fspec.mant})'
      elif isinstance(value.dtype, Bool):
        xvalue = f'pyxhdl.real_ifexp({xvalue}, 1.0, 0.0)'

    return f'to_float({xvalue}, {fspec.exp}, {fspec.mant})'

  def _to_integer(self, value, dtype):
    if isinstance(value, Value):
      if value.dtype == dtype:
        return self.svalue(value)
      elif isinstance(value.dtype, (Bool, Sint, Uint, Float)):
        return f'to_integer({self.svalue(value)})'
      elif isinstance(value.dtype, Bits):
        return f'to_integer(unsigned({self.svalue(value)}))'
      elif isinstance(value.dtype, Real):
        return f'integer({self.svalue(value)})'
      else:
        pyu.fatal(f'Unable to convert to integer: {value.dtype}')

    return str(value) if isinstance(value, int) else f'integer({value})'

  def _to_real(self, value, dtype):
    if isinstance(value, Value):
      if value.dtype == dtype:
        return self.svalue(value)
      elif isinstance(value.dtype, (Bool, Sint, Uint, Float)):
        return f'to_real({self.svalue(value)})'
      elif isinstance(value.dtype, Bits):
        return f'to_real(unsigned({self.svalue(value)}))'
      elif isinstance(value.dtype, Integer):
        return f'real({self.svalue(value)})'
      else:
        pyu.fatal(f'Unable to convert to real: {value.dtype}')

    return str(value) if isinstance(value, float) else f'real({value})'

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

      xvalue = flat2shape(parts, shape, '(', ')')
    elif isinstance(value, Value) and value.dtype.array_shape:
      shape, vshape = dtype.array_shape, value.dtype.array_shape
      if shape != vshape:
        pyu.fatal(f'Shape mismatch: {vshape} vs. {shape}')

      element_type = dtype.element_type()
      velement_type = value.dtype.element_type()
      avalue = paren(self.svalue(value))
      parts = []
      for idx in np.ndindex(shape):
        substr = ''.join(f'({x})' for x in idx)
        svalue = Value(velement_type, f'{avalue}{substr}')
        parts.append(self._scalar_cast(svalue, element_type))

      xvalue = flat2shape(parts, shape, '(', ')')
    else:
      xvalue = self._scalar_cast(unwrap(value), dtype)
      for _ in range(dtype.ndim - 1):
        xvalue = f'(others => {xvalue})'

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
      if isinstance(value.dtype, (Uint, Sint)):
        return f'to_hstring({xvalue})'
      if isinstance(value.dtype, (Bool, Bits, Integer, Real)):
        return f'to_string({xvalue})'
      if isinstance(value.dtype, Float):
        return f'to_string(to_real({xvalue}))'

    return self.quote_string(xvalue)

  def quote_string(self, s):
    es = s.replace('"', '""')
    return f'"{es}"'

  def eval_token(self, token):
    if token == 'NOW':
      return 'to_string(now)'

  def emit_finish(self):
    self.emit_code('std.env.finish;')

  def emit_wait_for(self, ts=None):
    if ts is not None:
      wts, tu = self._normalize_time(ts)
      self.emit_code(f'wait for {round(wts)} {tu};')
    else:
      self.emit_code('wait;')

  def emit_wait_rising(self, *args):
    sargs = self.build_args_string(lambda a: f'rising_edge({paren(a)})', ' or ', args)
    self.emit_code(f'wait until {sargs};')

  def emit_wait_falling(self, *args):
    sargs = self.build_args_string(lambda a: f'falling_edge({paren(a)})', ' or ', args)
    self.emit_code(f'wait until {sargs};')

  def emit_wait_until(self, *args):
    sargs = self.build_args_string(lambda a: paren(a), ' or ', args)
    self.emit_code(f'wait until {sargs};')

  def emit_report(self, parts, severity=None):
    self._emit_line('report ' + ' & '.join(parts) + ';')

  def emit_write(self, parts):
    self._emit_line('write(output, ' + ' & '.join(parts) + ' & LF);')

  def _gen_array_access(self, arg, idx):
    idx = pyu.as_sequence(idx)

    ashape = arg.dtype.shape
    if len(idx) > len(ashape):
      pyu.fatal(f'Wrong indexing for shape: {idx} vs. {ashape}')

    shape, coords = [], []
    for i, ix in enumerate(idx):
      if isinstance(ix, slice):
        if isinstance(ix.start, Value):
          if ix.stop is not None:
            pyu.fatal(f'Variable part select ({arg} [{i}]) slice stop must be empty: {ix.stop}')
          if ix.step > ashape[i]:
            pyu.fatal(f'Variable part select ({arg} [{i}]) is too big: {ix.step} ({ashape[i]})')

          base = self._to_integer(ix.start, Integer())

          if i == len(ashape) - 1:
            coords.append(f'({paren(base)} - {ix.step - 1}) downto {paren(base)}')
          else:
            coords.append(f'{paren(base)} to ({paren(base)} + {ix.step - 1})')

          shape.append(ix.step)
        else:
          step = ix.step if ix.step is not None else 1

          if abs(step) != 1:
            pyu.fatal(f'Slice step must be 1: {step}')

          start, stop = pycu.norm_slice(ix.start, ix.stop, ashape[i])
          if start < 0 or start >= ashape[i] or stop < 0 or stop > ashape[i]:
            pyu.fatal(f'Slice ({arg} [{i}]) is out of bounds: {start} ... {stop} ({ashape[i]})')

          if step == 1:
            if i == len(ashape) - 1:
              coords.append(f'{stop - 1} downto {start}')
            else:
              coords.append(f'{start} to {stop - 1}')
          else:
            if i == len(ashape) - 1:
              coords.append(f'{stop + 1} to {start}')
            else:
              coords.append(f'{start} downto {stop + 1}')

          shape.append(abs(stop - start))
      else:
        if isinstance(ix, Value) and not isinstance(ix.dtype, Integer):
          ix = self._to_integer(ix, Integer())

        coords.append(self.svalue(ix))
        shape.append(1)

    shape = pyu.squeeze(shape + list(arg.dtype.full_shape[len(idx): ]), keep_dims=1,
                        sdir=pyu.MAJOR)
    avalue = self.svalue(arg) + ''.join(f'({x})' for x in coords)

    return avalue, shape

  def flush(self):
    return self._load_libs() + self._expand()

  def is_root_variable(self, var):
    return var.isreg or var.is_const()

  def var_remap(self, var, is_store):
    return var

  def emit_declare_variable(self, name, var):
    vtype = self._type_of(var.dtype)

    if var.is_const():
      vprefix = 'constant'
    elif self._proc.kind == ROOT_PROCESS:
      vprefix = 'signal'
    else:
      vprefix = 'variable' if var.isreg is False else 'signal'

    if var.init is not None:
      xinit = self._cast(var.init, var.dtype)
      vinit = f' := {xinit}'
    else:
      vinit = ''

    self._emit_line(f'{vprefix} {name} : {vtype}{vinit};')

  def emit_assign(self, var, name, value):
    xvalue = self._cast(value, var.dtype)

    xdelay, xtrans = '', ''

    delay = self.get_context('delay')
    trans = self.get_context('trans')
    if delay is not None or trans is True:
      # Delays apply only to signals, not registers ...
      if var.isreg is False:
        pyu.fatal(f'Cannot use delay/trans on wires: {var}')
      if self._proc.kind == ROOT_PROCESS:
        pyu.fatal(f'Cannot use delay/trans within a root process: {var}')

      if delay is not None:
        xdelay = f' after {self.svalue(delay)} {self.time_unit()}'
      if trans is True:
        xtrans = 'transport '

    vspec = var.vspec
    if (vspec is not None and vspec.port is not None and vspec.port.is_wr()):
      asop = '<='
    else:
      asop = ':=' if var.isreg is False else '<='

    self._emit_line(f'{var.value} {asop} {xtrans}{xvalue}{xdelay};')

  def make_port_arg(self, port_arg):
    return port_arg.new_isreg(False)

  def emit_entity(self, ent, kwargs, ent_name=None):
    if ent_name is None:
      ent_name = pyiu.cname(ent)

    iname = self._get_entity_inst(ent_name)

    with self.placement(self._entity_place):
      self._emit_line(f'{iname} : entity {ent_name}')

      eparams = kwargs.pop(PARAM_KEY, None)
      if eparams is not None:
        self._emit_line(f'generic map (')
        with self.indent():
          for i, (k, v) in enumerate(eparams.items()):
            gmap = f'{k} => {v}' + ('' if i == len(eparams) - 1 else ',')
            self._emit_line(gmap)
        self._emit_line(f')')

      self._emit_line(f'port map (')
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
              pyu.fatal(f'Argument must be a Value subclass: {xarg}')

            if xarg.is_none():
              binds.append(f'{xpin.name} => open')
            else:
              earg = self.svalue(xarg)
              binds.append(f'{xpin.name} => {earg}')

        for i, port_bind in enumerate(binds):
          self._emit_line(port_bind + ('' if i == len(binds) - 1 else ','))

      self._emit_line(f');')

  def emit_module_def(self, name, ent, comment=None):
    self._emit_header()

    self._mod_comment = comment
    if comment:
      self.emit_comment(comment)
    self._emit_line(f'entity {name} is')
    if ent.args:
      with self.indent():
        self._emit_line(f'port (')
        with self.indent():
          xports = ent.expanded_ports()
          for i, ap in enumerate(xports):
            pin, arg = ap.port, ap.arg

            pdir = 'in' if pin.is_ro() else 'out' if pin.is_wo() else 'inout'
            ptype = self._type_of(arg.dtype)
            port_decl = f'{pin.name} : {pdir} {ptype}'

            self._emit_line(port_decl + (';' if i + 1 < len(xports) else ''))

        self._emit_line(f');')

    self._emit_line(f'end entity;')

  def emit_module_decl(self, name, ent):
    self._emit_header()

    if self._mod_comment:
      self.emit_comment(self._mod_comment)
    self._emit_line(f'architecture {self._arch} of {name} is')
    self.module_vars_place = self.emit_placement(extra_indent=1)

    self._emit_line(f'begin')

    self._entity_place = self.emit_placement(extra_indent=1)

  def emit_module_end(self):
    self._emit_line(f'end architecture;')

    self._mod_comment = None

  def emit_process_decl(self, name, sensitivity=None, process_kind=None,
                        process_args=None):
    self._process_init(name, process_kind, process_args, sensitivity)

    proc_decl = f'{name} : process'
    if sensitivity:
      proc_decl += ' (' + ', '.join(name for name in sensitivity.keys()) + ')'
    else:
      proc_mode = process_args.get('proc_mode') if process_args else None
      if proc_mode == 'comb':
        proc_decl += ' (all)'

    self._emit_line(proc_decl)
    self.process_vars_place = self.emit_placement(extra_indent=1)

  def emit_process_begin(self):
    self._emit_line(f'begin')
    if self._proc.sens:
      tests = []
      for name, sens in self._proc.sens.items():
        if sens.trigger == POSEDGE:
          tests.append(f'rising_edge({name})')
        elif sens.trigger == NEGEDGE:
          tests.append(f'falling_edge({name})')

      if tests:
        self._proc_indent += 1
        self._indent += 1
        self._emit_line('if ' + ' or '.join(tests) + ' then')

  def emit_process_end(self):
    # There is no special "init" process in VHDL, so we need to make sure that once
    # it ran, it stops.
    if self._proc.kind == INIT_PROCESS:
      with self.indent():
        self._emit_line('wait;')

    if self._proc_indent > 0:
      self._proc_indent -= 1
      self._emit_line('end if;')
      self._indent -= 1

    self._emit_line(f'end process;')

    self._process_reset()

  def emit_comment(self, msg):
    for ln in msg.split('\n'):
      self._emit_line(f'-- {ln}')

  def emit_If(self, test):
    xtest = self._cast(test, BOOL)
    self._emit_line(f'if {xtest} then')

  def emit_Elif(self, test):
    xtest = self._cast(test, BOOL)
    self._emit_line(f'elsif {xtest} then')

  def emit_Else(self):
    self._emit_line(f'else')

  def emit_EndIf(self):
    self._emit_line(f'end if;')

  def emit_Assert(self, test, parts):
    xtest = self.svalue(test)
    if parts:
      self._emit_line(f'assert {xtest} report ' + ' & '.join(parts) + ';')
    else:
      self._emit_line(f'assert {xtest};')

  def emit_match_cases(self, subject, cases):
    xsubject = self.svalue(subject)
    self._emit_line(f'case {paren(xsubject)} is')

    with self.indent():
      for mc in cases:
        if mc.pattern is not None:
          xpattern = self._cast(mc.pattern, subject.dtype)
          self._emit_line(f'when {paren(xpattern)} =>')
        else:
          self._emit_line(f'when others =>')

        if len(mc.scope) == 0:
          with self.placement(mc.scope):
            self._emit_line(f'null;')

        self._emit(mc.scope)

    self._emit_line(f'end case;')

  def _build_op(self, op, left, right):
    sop = _OPSYMS[pyiu.classof(op)]
    if sop.isfn:
      return f'{sop.sym}({paren(left)}, {paren(right)})'
    else:
      return f'{paren(left)} {sop.sym} {paren(right)}'

  def eval_BinOp(self, op, left, right):
    if isinstance(op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod)):
      left, right = self._marshal_arith_op([left, right],
                                           ctype_nocast=_ARITH_CTYPE_NOCAST)
      xleft, xright = self.svalue(left), self.svalue(right)

      pyu.mlog(lambda: f'\tBinOp: {xleft}\t{pyiu.cname(op)}\t{xright}')
      result = self._build_op(op, xleft, xright)
      # The signed/unsigned multiplication result has a number of bits which is the
      # sum of the ones of the operands, which is not the behaviour we want.
      if isinstance(op, ast.Mult) and isinstance(left.dtype, (Sint, Uint)):
        result = f'resize({result}, {left.dtype.nbits})'

      return Value(left.dtype, result)
    elif isinstance(op, (ast.LShift, ast.RShift)):
      left, right = self._marshal_shift_op(left, right)
      xleft, xright = self.svalue(left), self.svalue(right)

      pyu.mlog(lambda: f'\tBinOp: {xleft}\t{pyiu.cname(op)}\t{xright}')

      return Value(left.dtype, self._build_op(op, xleft, xright))
    elif isinstance(op, (ast.BitOr, ast.BitXor, ast.BitAnd)):
      left, right = self._marshal_bit_op([left, right])
      xleft, xright = self.svalue(left), self.svalue(right)

      pyu.mlog(lambda: f'\tBinOp: {xleft}\t{pyiu.cname(op)}\t{xright}')

      return Value(left.dtype, self._build_op(op, xleft, xright))
    elif isinstance(op, ast.MatMult):
      # Steal MatMult ('@') for concatenation!
      dtype, (left, right) = self._marshal_concat_op([left, right])
      xleft, xright = self.svalue(left), self.svalue(right)

      pyu.mlog(lambda: f'\tBinOp: {xleft}\t{pyiu.cname(op)}\t{xright}')

      return Value(dtype, self._build_op(op, xleft, xright))
    else:
      pyu.fatal(f'Unsupported operation: {op}')

  def eval_UnaryOp(self, op, arg):
    xvalue = self.svalue(arg)

    pyu.mlog(lambda: f'\tUnaryOp: {pyiu.cname(op)}\t{xvalue}')

    if isinstance(op, ast.UAdd):
      # Unary addition is a noop for HDL data types.
      result = xvalue
    elif isinstance(op, ast.USub):
      result = f'-{paren(xvalue)}'
    elif isinstance(op, (ast.Not, ast.Invert)):
      result = f'not {paren(xvalue)}'
    else:
      pyu.fatal(f'Unsupported operation: {op}')

    return Value(arg.dtype, result)

  def eval_BoolOp(self, op, args):
    xargs = [self._cast(a, BOOL) for a in args]

    pyu.mlog(lambda: f'\tBoolOp: {pyiu.cname(op)}\t{pyu.stri(xargs)}')

    if isinstance(op, ast.And):
      result = self._paren_join(' and ', xargs)
    elif isinstance(op, ast.Or):
      result = self._paren_join(' or ', xargs)
    else:
      pyu.fatal(f'Unsupported operation: {op}')

    return Value(BOOL, result)

  def eval_Compare(self, left, ops, comps):
    comps = self._marshal_compare_op([left] + list(comps))
    xcomps = [self.svalue(comp) for comp in comps]

    pyu.mlog(lambda: f'\tCompare: {[pyiu.cname(x) for x in ops]}\t{pyu.stri(xcomps)}')

    results = []
    for i, op in enumerate(ops):
      cres = self._build_op(op, xcomps[i], xcomps[i + 1])
      results.append(cres)

    result = self._paren_join(' and ', results)

    return Value(BOOL, result)

  def eval_Subscript(self, arg, idx):
    result, shape = self._gen_array_access(arg, idx)

    return arg.new_value(result, shape=shape, keepref=True)

  def eval_IfExp(self, test, body, orelse):
    xtest = self.svalue(test)
    body, orelse = self._marshal_ifexp_op([body, orelse])
    xbody, xorelse = self.svalue(body), self.svalue(orelse)

    pyu.mlog(lambda: f'\tIfExp: {xtest} ? {xbody} : {xorelse}')

    result = f'pyxhdl.{body.dtype.name}_ifexp({xtest}, {xbody}, {xorelse})'

    return Value(body.dtype, result)

  # Extension functions.
  def eval_is_nan(self, value):
    if not isinstance(value.dtype, Float):
      pyu.fatal(f'Unsupported type: {value.dtype}')

    result = f'Isnan({self.svalue(value)})'

    return Value(BOOL, result)

  def eval_is_inf(self, value):
    if not isinstance(value.dtype, Float):
      pyu.fatal(f'Unsupported type: {value.dtype}')

    result = f'not Finite({self.svalue(value)})'

    return Value(BOOL, result)


# Register VHDL (VHDL >= 2008) emitter class.
Emitter.register('vhdl', VHDL_Emitter)

