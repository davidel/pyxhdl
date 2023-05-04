import collections
import logging

import py_misc_utils.utils as pyu

from .types import *
from .value_base import *


# Must have defaults for all fields!
VSpec = collections.namedtuple('VSpec', 'const, port', defaults=[False, None])


def _mode(mode, vspec):
  if mode is None:
    mode = Ref.RW if vspec is None or not vspec.const else Ref.RO

  return mode


class Ref(object):

  RW = 1
  RO = 2

  def __init__(self, name, mode=None, vspec=None):
    self.name = name
    self.mode = _mode(mode, vspec)
    self.vspec = vspec

  def __str__(self):
    return f'${self.name}' if self.mode == Ref.RW else f'#{self.name}'

  def __hash__(self):
    return hash((self.name, self.mode, self.vspec))

  def __eq__(self, other):
    return self.name == other.name and self.mode == other.mode and self.vspec == other.vspec

  def new_name(self, name):
    return pyu.new_with(self, name=name)

  def new_mode(self, mode):
    return pyu.new_with(self, mode=mode)


class Init(object):

  def __init__(self, value=None, vspec=None):
    self.value = value
    self.vspec = vspec

  def __hash__(self):
    return hash((self.value, self.vspec))

  def __eq__(self, other):
    return self.value == other.value and self.vspec == other.vspec

  def __str__(self):
    return f'{self.value}' if self.vspec is None else f'({self.value}, {self.vspec})'


class Value(ValueBase):

  def __init__(self, dtype, value=None, isreg=None):
    super().__init__()
    self._dtype = dtype
    self._value = value
    self._isreg = isreg

  @property
  def dtype(self):
    return self._dtype

  @property
  def value(self):
    v = self._value
    return v.name if isinstance(v, Ref) else v

  @property
  def ref(self):
    v = self._value
    return v if isinstance(v, Ref) else None

  @property
  def init(self):
    v = self._value
    return v if isinstance(v, Init) else None

  @property
  def name(self):
    v = self._value
    return v.name if isinstance(v, Ref) else None

  @property
  def isreg(self):
    return self._isreg

  def __str__(self):
    return f'{pyu.cname(self)}({self._value}, dtype={self._dtype}, isreg={self.isreg})'

  def __hash__(self):
    return hash((self._dtype, self._value, self._isreg))

  def __eq__(self, other):
    return (self.dtype == other.dtype and self.value == other.value and
            self.isreg == other.isreg)

  def deref(self):
    # Dereferencing a Value which is a reference, drops the reference and the reg/wire
    # status (isreg == None means temp value).
    ref = self.ref

    return pyu.new_with(self, _value=ref.name, _isreg=None) if ref is not None else self

  def new_value(self, value, shape=None):
    dtype = self._dtype.new_shape(*shape) if shape is not None else self._dtype

    return pyu.new_with(self, _value=value, _dtype=dtype)

  def new_isreg(self, isreg):
    return pyu.new_with(self, _isreg=isreg)


class Wire(Value):

  def __init__(self, dtype, value=None):
    super().__init__(dtype, value=value, isreg=False)


class Register(Value):

  def __init__(self, dtype, value=None):
    super().__init__(dtype, value=value, isreg=True)


def valkind(isreg):
  return 'REG' if isreg is True else 'WIRE' if isreg is False else 'TEMP'


def _init_value(name, iargs):
  vspec = pyu.make_ntuple(VSpec, iargs or dict())

  return Ref(name, vspec=vspec) if name is not None else Init(vspec=vspec)


def mkwire(dtype, name=None, **iargs):
  return Wire(dtype, value=_init_value(name, iargs))


def mkreg(dtype, name=None, **iargs):
  return Register(dtype, value=_init_value(name, iargs))


def make_ro_ref(v):
  ref = v.ref
  if ref is not None and ref.mode == Ref.RW:
    return v.new_value(ref.new_mode(Ref.RO))

  return v


def is_ro_ref(v):
  ref = v.ref

  return ref is not None and ref.mode == Ref.RO


def has_hdl_vars(v):
  if isinstance(v, Value):
    return True
  elif isinstance(v, (list, tuple, set)):
    for e in v:
      if has_hdl_vars(e):
        return True
  elif isinstance(v, dict):
    for k, u in v.items():
      if has_hdl_vars(k) or has_hdl_vars(u):
        return True

  return False

