import re

import py_misc_utils.core_utils as pycu
import py_misc_utils.inspect_utils as pyiu
import py_misc_utils.utils as pyu

from .types import *
from .value_base import *


class VSpec:

  __slots__ = ('const', 'port')

  def __init__(self, const=False, port=None):
    self.const = const
    self.port = port

  def __repr__(self):
    rfmt = pyu.repr_fmt(self, 'const,port')

    return f'{pyiu.cname(self)}({rfmt})'

  def __hash__(self):
    return hash((self.const, self.port))

  def __eq__(self, other):
    return self.const == other.const and self.port == other.port


class Ref:

  __slots__ = ('name', 'mode', 'vspec', 'cname', 'vname')

  RW = 'RW'
  RO = 'RO'

  def __init__(self, name, mode=None, vspec=None, cname=None, vname=None):
    self.name = name
    self.mode = self._mode(mode, vspec)
    self.vspec = vspec
    self.cname = cname
    self.vname = vname

  @classmethod
  def _mode(cls, mode, vspec):
    if mode is None:
      mode = cls.RW if vspec is None or not vspec.const else cls.RO

    return mode

  def __repr__(self):
    rfmt = pyu.repr_fmt(self, 'name=,mode,vspec,cname,vname')

    return f'{pyiu.cname(self)}({rfmt})'

  def __hash__(self):
    return hash((self.name, self.mode, self.vspec, self.cname, self.vname))

  def __eq__(self, other):
    return (self.name == other.name and self.mode == other.mode and
            self.vspec == other.vspec and self.cname == other.cname and
            self.vname == other.vname)

  def new_name(self, name, vname=None):
    return pycu.new_with(self, name=name, vname=vname, cname=None)

  def new_mode(self, mode):
    return pycu.new_with(self, mode=mode)


class Init:

  __slots__ = ('value', 'name', 'vspec')

  def __init__(self, value=None, name=None, vspec=None):
    self.value = value
    self.name = name
    self.vspec = vspec

  def __hash__(self):
    return hash((self.value, self.name, self.vspec))

  def __eq__(self, other):
    return (self.value == other.value and self.name == other.name and
            self.vspec == other.vspec)

  def __repr__(self):
    rfmt = pyu.repr_fmt(self, 'value=,name,vspec')

    return f'{pyiu.cname(self)}({rfmt})'


class Value(ValueBase):

  __slots__ = ('dtype', '_value', 'isreg')

  def __init__(self, dtype, value, isreg=None):
    super().__init__()
    self.dtype = dtype
    self._value = value
    self.isreg = isreg

  @property
  def value(self):
    v = self._value
    return v.name if isinstance(v, Ref) else v

  @property
  def ref(self):
    v = self._value
    return v if isinstance(v, Ref) else None

  @property
  def vspec(self):
    v = self._value
    return v.vspec if isinstance(v, Ref) else None

  @property
  def init(self):
    v = self._value
    return v if isinstance(v, Init) else None

  @property
  def name(self):
    v = self._value
    return v.vname if isinstance(v, Ref) else None

  def __repr__(self):
    rfmt = pyu.repr_fmt(self, '_value=,dtype,isreg')

    return f'{pyiu.cname(self)}({rfmt})'

  def __hash__(self):
    return hash((self.dtype, self._value, self.isreg))

  def __eq__(self, other):
    return (self.dtype == other.dtype and self._value == other._value and
            self.isreg == other.isreg)

  def new_value(self, value, shape=None, keepref=False):
    dtype = self.dtype.new_shape(*shape) if shape is not None else self.dtype

    if keepref and not isinstance(value, Ref):
      ref = self.ref
      if ref is not None:
        value = ref.new_name(value)

    return pycu.new_with(self, _value=value, dtype=dtype)

  def new_isreg(self, isreg):
    return pycu.new_with(self, isreg=isreg)


class Wire(Value):

  def __init__(self, dtype, value):
    super().__init__(dtype, value, isreg=False)


class Register(Value):

  def __init__(self, dtype, value):
    super().__init__(dtype, value, isreg=True)


def valkind(isreg):
  return 'REG' if isreg is True else 'WIRE' if isreg is False else 'TEMP'


def _init_value(name, iargs):
  vspec = VSpec(**(iargs or dict()))

  return (Ref(name, vspec=vspec, cname=name, vname=name) if name is not None
          else Init(vspec=vspec))


def mkwire(dtype, name=None, **iargs):
  return Wire(dtype, _init_value(name, iargs))


def mkreg(dtype, name=None, **iargs):
  return Register(dtype, _init_value(name, iargs))


def mkvwire(dtype, value, name=None, **iargs):
  vspec = VSpec(**(iargs or dict()))

  return Wire(dtype, Init(value=value, vspec=vspec, name=name))


def mkvreg(dtype, value, name=None, **iargs):
  vspec = VSpec(**(iargs or dict()))

  return Register(dtype, Init(value=value, vspec=vspec, name=name))


def make_ro_ref(v):
  vref = v.ref
  if vref is not None and vref.mode == Ref.RW:
    return v.new_value(vref.new_mode(Ref.RO))

  return v


def is_ro_ref(v):
  vref = v.ref

  return vref is not None and vref.mode == Ref.RO


def has_hdl_vars(v):
  if isinstance(v, Value):
    return True
  elif isinstance(v, (list, tuple, set)):
    for e in v:
      if has_hdl_vars(e):
        return True
  elif pycu.isdict(v):
    for k, u in v.items():
      if has_hdl_vars(k) or has_hdl_vars(u):
        return True

  return False


def bitstring(value, remap=None):
  # 0b0010 -> dtype=Bits(4), value="0010"
  m = re.match(r'0b([01XUZWHL]+)$', value)
  if m:
    bstr = ''.join(remap(x) for x in m.group(1)) if remap is not None else m.group(1)

    return Value(Bits(len(bstr)), bstr)


def bitfill(bitval, n):
  return '0b' + bitval * n

