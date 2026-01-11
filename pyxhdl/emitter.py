import ast
import collections
import functools
import inspect
import os

import py_misc_utils.alog as alog
import py_misc_utils.context_managers as pycm
import py_misc_utils.inspect_utils as pyiu
import py_misc_utils.obj as obj
import py_misc_utils.template_replace as pytr
import py_misc_utils.utils as pyu

from .pyxhdl import *
from .types import *
from .vars import *
from .utils import *


# For VHDL we mean VHDL >= 2008.
VHDL = 'VHDL'
# For Verilog we mean SystemVerilog >= 2012.
VERILOG = 'Verilog'

PARAM_KEY = '_P'

OpSym = collections.namedtuple('OpSym', 'sym, isfn', defaults=[False])

FSpec = collections.namedtuple('FSpec', 'exp, mant')

_ProcessInfo = collections.namedtuple('ProcessInfo', 'name, kind, args, sens',
                                      defaults=[None, ROOT_PROCESS, None, None])

_Prec = collections.namedtuple('Prec', 'prec, prio, rtype', defaults=[0, None])

_ARITH_TYPE_PREC = {
  Bool: _Prec(-1, rtype=Uint(1)),
  Sint: _Prec(1, 2),
  Uint: _Prec(1, 1),
  Integer: _Prec(2),
  Float: _Prec(3),
  Real: _Prec(4),
}

_BIT_TYPE_PREC = {
  Bool: _Prec(-1, rtype=Uint(1)),
  Sint: _Prec(1, 1),
  Uint: _Prec(1, 2),
  Bits: _Prec(1, 3),
}

_CONCAT_TYPE_PREC = {
  Bool: _Prec(-1, rtype=Bits(1)),
  Sint: _Prec(1),
  Uint: _Prec(2),
  Bits: _Prec(3),
}

_COMPARE_TYPE_PREC = {
  Bool: _Prec(-1),
  Bits: _Prec(1),
  Sint: _Prec(2, 2),
  Uint: _Prec(2, 1),
  Integer: _Prec(3),
  Float: _Prec(4),
  Real: _Prec(5),
}

_IFEXP_TYPE_PREC = {
  Bool: _Prec(1),
  Sint: _Prec(2, 2),
  Uint: _Prec(2, 1),
  Integer: _Prec(3),
  Float: _Prec(4),
  Real: _Prec(5),
  Bits: _Prec(6),
}

_CTYPES_ALLOWED = {
  float: 1,
  int: 2,
}

_FLOAT_SPECS = {
  16: FSpec(5, 10),
  32: FSpec(8, 23),
  64: FSpec(11, 52),
  80: FSpec(17, 63),
  128: FSpec(15, 112),
}

class _Placement:

  def __init__(self, indent=None):
    self.code = []
    self.indent = indent

  def __len__(self):
    count = 0
    for c in self.code:
      if isinstance(c, _Placement):
        count += len(c)
      else:
        count += 1

    return count


class Emitter:

  _BACKEND_REGISTRY = dict()
  _MODULE_REGISTRY = collections.defaultdict(dict)

  def __init__(self, cfg_file=None, **kwargs):
    self._cfg_file = cfg_file
    self._cfg = pyu.load_config(cfg_file, extra=kwargs) if cfg_file else dict()
    self._indent_spaces = self._cfg.get('indent_spaces', 2)
    self._indent = 0
    self._placements = []
    self._code = []
    self._ent_versions = collections.defaultdict(int)
    self._user_modules = collections.defaultdict(dict)
    self._contexts = []
    self._proc = _ProcessInfo()

  @classmethod
  def register(cls, name, eclass):
    cls._BACKEND_REGISTRY[name] = eclass

  @classmethod
  def available(cls):
    return sorted(cls._BACKEND_REGISTRY.keys())

  @classmethod
  def create(cls, name, **kwargs):
    eclass = cls._BACKEND_REGISTRY.get(name, None)
    if eclass is None:
      pyu.fatal(f'Unknown emitter: {name}')

    return eclass(**kwargs)

  @classmethod
  def _register_module(cls, mid, code, dest, replace):
    for kind, kcode in code.items():
      mdict = dest[kind]
      if mid in mdict:
        if replace is False:
          pyu.fatal(f'Module "{mid}" already registered')
        else:
          alog.info(f'Module "{mid}" already registered, overriding!')

      mdict[mid] = kcode.split('\n')

  @classmethod
  def glob_register_module(cls, mid, code, replace=None):
    cls._register_module(mid, code, cls._MODULE_REGISTRY, replace=replace)

  def register_module(self, mid, code, replace=None):
    self._register_module(mid, code, self._user_modules, replace=replace)

  def float_spec(self, dtype):
    fsenv = os.getenv(f'F{dtype.nbits}_SPEC', None)
    if fsenv is not None:
      return FSpec(int(x.strip()) for x in fsenv.split(','))

    fspecs = self._cfg.get('float_specs', _FLOAT_SPECS)
    fspec = fspecs.get(dtype.nbits, None)
    if fspec is None:
      pyu.fatal(f'Unknown floating point spec: {dtype.nbits} bits',
                exc=TypeError)

    return fspec

  def get_contexts(self, kind):
    all_contexts = []
    for ctx in self._contexts:
      kctx = ctx.get(kind, None)
      if kctx is not None:
        all_contexts.append(kctx)

    return all_contexts

  def get_context(self, kind, defval=None):
    ctxs = self.get_contexts(kind)

    return ctxs[-1] if ctxs else defval

  def create_placement(self, extra_indent=0):
    return _Placement(indent=self._indent + extra_indent)

  def emit_placement(self, placement=None, extra_indent=0):
    place = self.create_placement(extra_indent=extra_indent)
    self._emit(place, placement=placement)

    return place

  def _emit(self, obj, placement=None):
    if placement is None:
      self._code.append(obj)
    else:
      placement.code.append(obj)

  def _emit_line(self, line):
    spaces = ' ' * (self._indent_spaces * self._indent)
    if not self._placements:
      self._emit(spaces + line)
    else:
      self._emit(spaces + line, placement=self._placements[-1])

  def _expand_helper(self, code, lines):
    for ent in code:
      if isinstance(ent, _Placement):
        self._expand_helper(ent.code, lines)
      elif isinstance(ent, (list, tuple)):
        self._expand_helper(ent, lines)
      else:
        lines.append(ent)

    return lines

  def _expand(self):
    lines = []

    return self._expand_helper(self._code, lines)

  def _process_init(self, name, kind, args, sens):
    self._proc = _ProcessInfo(name=name, kind=kind, args=args, sens=sens)

  def _process_reset(self):
    self._proc = _ProcessInfo()

  def _paren_join(self, joiner, args):
    return joiner.join(paren(x) for x in args) if len(args) > 1 else args[0]

  def _default_float_type(self):
    return dtype_from_string(os.getenv('FLOAT_TYPE', 'f32'))

  def _match_bitstring(self, value, remap=None):
    # 0b0010 -> dtype=Bits(4), value="0010"
    m = re.match(r'0b([01XUZWHL]+)$', value)
    if m:
      return ''.join(remap(x) for x in m.group(1)) if remap is not None else m.group(1)

  def _match_intstring(self, value):
    dtype, ivalue = None, None
    # u16`1234 -> dtype=Uint(16), ivalue=1234
    m = re.match(r'([us])(\d+)`(.*)$', value)
    if m:
      nbits = int(m.group(2))
      ivalue = ast.literal_eval(m.group(3))
      if not isinstance(ivalue, int): pyu.fatal(f'Invalid literal value: {value}')
      if m.group(1) == 'u':
        dtype = Uint(nbits)
      else:
        dtype = Sint(nbits)

    return dtype, ivalue

  def _convert_int(self, value, tclass=None):
    if tclass is None:
      tclass = Uint if value >= 0 else Sint

    return Value(tclass(value.bit_length()), value=str(value))

  def _best_type(self, cur, new, type_prec):
    nprec = type_prec.get(type(new), None)
    if nprec is None:
      pyu.fatal(f'Unsupported type {pyiu.cname(new)} ... should be ' \
                f'{tuple(pyiu.cname(x) for x in type_prec.keys())}')
    if cur is not None:
      cprec = type_prec[type(cur)]
      dprec = nprec.prec - cprec.prec
      if dprec > 0:
        return new
      elif dprec < 0:
        return cur
      elif new.nbits > cur.nbits:
        return new
      elif new.nbits < cur.nbits:
        return cur
      else:
        return new if nprec.prio > cprec.prio else cur

    return new

  def _result_type(self, dtype, type_prec):
    if dtype is not None:
      prec = type_prec.get(type(dtype), None)
      if prec is not None and prec.rtype is not None:
        dtype = prec.rtype

    return dtype

  def _marshal_arith_op(self, args, ctype_allowed=None, ctype_nocast=None):
    return self._gen_marshal(args, _ARITH_TYPE_PREC, ctype_allowed or _CTYPES_ALLOWED,
                             ctype_nocast=ctype_nocast)

  def _marshal_concat_op(self, args):
    dtype, margs, nbits = None, [], 0
    for arg in args:
      if not isinstance(arg, Value):
        arg = self._try_convert_literal(arg)
        if not isinstance(arg, Value):
          pyu.assert_instance('Integer type required', arg, int)
          arg = self._convert_int(arg)

      margs.append(arg)
      nbits += arg.dtype.nbits
      dtype = self._best_type(dtype, arg.dtype, _CONCAT_TYPE_PREC)

    dtype = self._result_type(dtype, _CONCAT_TYPE_PREC)

    tclass = type(dtype)
    for i, arg in enumerate(margs):
      if type(arg.dtype) != tclass:
        atype = tclass(arg.dtype.nbits)
        margs[i] = Value(atype, value=self._cast(arg, atype))

    return tclass(nbits), margs

  def _marshal_bit_op(self, args):
    dtype, margs = None, []
    for arg in args:
      if not isinstance(arg, Value):
        arg = self._try_convert_literal(arg)
      margs.append(arg)
      if isinstance(arg, Value):
        dtype = self._best_type(dtype, arg.dtype, _BIT_TYPE_PREC)
      else:
        pyu.assert_instance('Integer type required', arg, int)

    dtype = self._result_type(dtype, _BIT_TYPE_PREC)
    if dtype is None:
      nbits = max(arg.bit_length() for arg in args)
      dtype = Uint(nbits)

    return [Value(dtype, value=self._cast(arg, dtype)) for arg in margs]

  def _marshal_shift_op(self, left, right):
    if isinstance(right, Value):
      if not isinstance(right.dtype, Integer):
        rdtype = Integer()
        right = Value(rdtype, value=self._cast(right, rdtype))
    elif type(right) != int:
      pyu.fatal(f'Shift amount should be an integer: {right}')
    if not isinstance(left, Value):
      left = self._try_convert_literal(arg)
      if not isinstance(left, Value):
        pyu.assert_instance('Shift operand should be an integer', left, int)
        dtype = Uint(left.bit_length())
        left = Value(dtype, value=self._cast(left, dtype))
      else:
        pyu.assert_instance('Unexpected type', left.dtype, (Bits, Sint, Uint, Integer))

    return left, right

  def _marshal_compare_op(self, args, ctype_allowed=None, ctype_nocast=None):
    return self._gen_marshal(args, _COMPARE_TYPE_PREC, ctype_allowed or _CTYPES_ALLOWED,
                             ctype_nocast=ctype_nocast)

  def _marshal_ifexp_op(self, args, ctype_allowed=None, ctype_nocast=None):
    return self._gen_marshal(args, _IFEXP_TYPE_PREC, ctype_allowed or _CTYPES_ALLOWED,
                             ctype_nocast=ctype_nocast)

  def _gen_marshal(self, args, type_prec, ctype_allowed, ctype_nocast=None):
    cargs, dtype, ctype = [], None, None
    for arg in args:
      if not isinstance(arg, Value):
        arg = self._try_convert_literal(arg)
      cargs.append(arg)
      if isinstance(arg, Value):
        dtype = self._best_type(dtype, arg.dtype, type_prec)
      else:
        ytype = type(arg)
        yind = ctype_allowed.get(ytype, -1)
        if yind < 0:
          pyu.fatal(f'Type {ytype} not allowed, should be one of {ctype_allowed.keys()}')
        if ctype is None or ctype_allowed[ctype] > yind:
          ctype = ytype

    dtype = self._result_type(dtype, type_prec)
    if dtype is None:
      if ctype == float:
        dtype = Real()
      elif ctype == int:
        dtype = Integer()
      else:
        pyu.fatal(f'Unknown type: {ctype}')

    for i, arg in enumerate(cargs):
      if isinstance(arg, Value):
        if dtype != arg.dtype:
          cargs[i] = Value(dtype, value=self._cast(arg, dtype))
      elif self._is_nocast(arg, dtype, ctype_nocast):
        cargs[i] = Value(dtype, value=dtype.ctype(arg))
      else:
        cargs[i] = Value(dtype, value=self._cast(arg, dtype))

    return cargs

  def _is_nocast(self, arg, dtype, ctype_nocast):
    return type(dtype) in ctype_nocast.get(type(arg), {}) if ctype_nocast else False

  def _cfg_lookup(self, k, defval=None):
    v = pyu.dict_rget(self._cfg, f'env/{k}')
    if v is None:
      v = os.getenv(f'PYXHDL_{k}', None)
      if v is None:
        if defval is None:
          pyu.fatal(f'Missing configuration: {k}')
        else:
          v = defval

    return v

  def _load_code(self, path):
    with open(path, mode='r') as fd:
      code = fd.read()

    return pytr.template_replace(code, lookup_fn=self._cfg_lookup, delim='@')

  def _load_libs(self, extra_libs=tuple()):
    pkgdir = os.path.dirname(__file__)
    libdir = os.path.join(pkgdir, 'hdl_libs', self.kind)
    pyu.mlog(lambda: f'Using {self.kind} library folder {libdir}')

    libcode, loaded = [], set()

    # Loading internal libraries by manifest (always load ones).
    libs_manifest_path = os.path.join(libdir, 'LIBS')
    if os.path.exists(libs_manifest_path):
      with open(libs_manifest_path, mode='r') as mfd:
        libs = [l.strip() for l in mfd.read().split('\n')]

      for libfname in libs:
        if libfname and not libfname.startswith('#'):
          lpath = os.path.join(libdir, libfname)
          pyu.mlog(lambda: f'Loading {self.kind} library file {lpath}')
          libcode.extend(self._load_code(lpath).split('\n'))
          loaded.add(os.path.splitext(libfname)[0])

    # Loading on-demand ones (always loading certain libraries can cause synthesis
    # failure even when such code is not used).
    lib_paths = [libdir]
    lpaths = os.getenv(f'PYXHDL_{self.kind}_LIBPATH', None)
    if lpaths is not None:
      lib_paths.extend(lpaths.split(';'))

    for libname in pyu.enum_set(extra_libs, loaded, False):
      libfname, llsize = libname + self.file_ext, len(loaded)
      for path in lib_paths:
        lpath = os.path.join(path, libfname)
        if os.path.isfile(lpath):
          pyu.mlog(lambda: f'Loading {self.kind} library file {lpath}')
          libcode.extend(self._load_code(lpath).split('\n'))
          loaded.add(libname)
          break

      if llsize == len(loaded):
        alog.info(f'Library "{libname}" not found, assuming internal')

    # Load user injected external libraries.
    cpath = os.path.dirname(self._cfg_file or __file__)
    ulibs = os.getenv(f'PYXHDL_{self.kind}_LIBS', None)
    if ulibs:
      for lpath in ulibs.split(';'):
        if not os.path.isabs(lpath):
          lpath = os.path.abspath(os.path.join(cpath, lpath))

        pyu.mlog(lambda: f'Loading {self.kind} library file {lpath}')
        libcode.extend(self._load_code(lpath).split('\n'))

    for lpath in self._cfg.get('libs', dict()).get(self.kind, []):
      if not os.path.isabs(lpath):
        lpath = os.path.abspath(os.path.join(cpath, lpath))

      pyu.mlog(lambda: f'Loading {self.kind} library file {lpath}')
      libcode.extend(self._load_code(lpath).split('\n'))

    # Add user defined modules within the PyXHDL code.
    for cid, umod in self._MODULE_REGISTRY[self.kind].items():
      libcode.extend(umod)
    for cid, umod in self._user_modules[self.kind].items():
      libcode.extend(umod)

    return libcode

  def _get_entity_inst(self, name):
    self._ent_versions[name] += 1

    return f'{name}_{self._ent_versions[name]}'

  def context(self, ctx):
    def infn():
      self._contexts.append(ctx)
      return self

    def outfn(*exc):
      self._contexts.pop()
      return False

    return pycm.CtxManager(infn, outfn)

  def placement(self, place):
    ctx = obj.Obj()

    def infn():
      self._placements.append(place)
      ctx.indent, self._indent = self._indent, place.indent
      return self

    def outfn(*exc):
      self._indent = ctx.indent
      self._placements.pop()
      return False

    return pycm.CtxManager(infn, outfn)

  def indent(self):
    def infn():
      self._indent += 1
      return self

    def outfn(*exc):
      self._indent -= 1
      return False

    return pycm.CtxManager(infn, outfn)

  def emit_code(self, code):
    for ln in code.split('\n'):
      self._emit_line(ln)

  def build_args_string(self, fn, delim, args):
    sargs = [fn(self.svalue(a)) for a in args]

    return delim.join(sargs)

  def emit_call(self, fname, args, dtype):
    cargs = self.build_args_string(lambda a: a, ', ', args)

    call = f'{fname}({cargs})'

    pyu.mlog(lambda: f'{call} -> {dtype}')

    # None return type means no return value call, which is emitted directly.
    # Otherwise it is a function, which returns a Value, which materializes only
    # when/if used (ie, within an expression or as RHS of an assignment).
    # This means that if an external function has side effects (ie, output arguments)
    # and a return value, such return value must be used (assigned to something or
    # used within an expression) in order to the side effects to manifest.
    if dtype is None:
      self.emit_code(f'{call}{self.eol}')
    else:
      return Value(dtype, value=call)

  def tclass_cast(self, tclass, value):
    # The input `value` here is a Python literal, not a Value.
    if tclass in (Sint, Uint):
      value = int(value)
      dtype = tclass(value.bit_length())
    elif tclass == Bits:
      if isinstance(value, int):
        nbits = value.bit_length()
      else:
        nbits = len(value) - (2 if value.startswith('0b') else 0)
      dtype = Bits(nbits)
    elif tclass == Float:
      dtype = self._default_float_type()
    elif tclass in (Bool, Integer, Real):
      dtype = tclass()
    else:
      pyu.fatal(f'Unsupported class "{pyiu.cname(tclass)}" while converting "{value}"')

    return self.cast(value, dtype)

  def time_unit(self):
    return self._cfg_lookup('TIME_UNIT', defval='ns')

