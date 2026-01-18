import inspect
import re

import numpy as np

import py_misc_utils.core_utils as pycu
import py_misc_utils.inspect_utils as pyiu
import py_misc_utils.utils as pyu


class Type:

  __slots__ = ('name', 'full_shape', 'ctype')

  def __init__(self, name, shape, ctype):
    self.name = name
    self.full_shape = tuple(shape[:])
    self.ctype = ctype

  @property
  def has_bits(self):
    return self.full_shape[-1] is not None

  @property
  def shape(self):
    return self.full_shape if self.has_bits else self.full_shape[: -1]

  @property
  def array_shape(self):
    return self.full_shape[: -1]

  @property
  def ndim(self):
    return len(self.full_shape) - (0 if self.has_bits else 1)

  @property
  def nbits(self):
    return self.full_shape[-1] if self.has_bits else 0

  @property
  def size(self):
    return np.prod(self.full_shape[: -1])

  def __eq__(self, other):
    return (self.name == other.name and self.full_shape == other.full_shape and
            self.ctype == other.ctype)

  def __str__(self):
    return f'{self.name}(' + ', '.join(str(x) for x in self.shape) + ')'

  def __repr__(self):
    return f'{pyiu.cname(self)}({self.name}, {self.full_shape}, {self.ctype})'

  def __hash__(self):
    return hash((self.name, self.full_shape, self.ctype))

  def new_shape(self, *shape):
    if not self.has_bits and (not shape or shape[-1] is not None):
      shape = shape + (None,)

    return pycu.new_with(self, full_shape=shape)

  def element_type(self):
    return self.new_shape(*self.full_shape[-1: ])


class Sint(Type):

  def __init__(self, *shape):
    super().__init__('sint', shape, int)


class Uint(Type):

  def __init__(self, *shape):
    super().__init__('uint', shape, int)


class Bits(Type):

  def __init__(self, *shape):
    super().__init__('bits', shape, int)


class Float(Type):

  def __init__(self, *shape):
    super().__init__('float', shape, float)


class Bool(Type):

  def __init__(self, *shape):
    super().__init__('bool', shape + (None,), bool)


class Integer(Type):

  def __init__(self, *shape):
    super().__init__('integer', shape + (None,), int)


class Real(Type):

  def __init__(self, *shape):
    super().__init__('real', shape + (None,), float)


class Void(Type):

  def __init__(self):
    super().__init__('void', (None,), None.__class__)


INT4 = Sint(4)
INT8 = Sint(8)
INT16 = Sint(16)
INT32 = Sint(32)
INT64 = Sint(64)
INT128 = Sint(128)

UINT4 = Uint(4)
UINT8 = Uint(8)
UINT16 = Uint(16)
UINT32 = Uint(32)
UINT64 = Uint(64)
UINT128 = Uint(128)

FLOAT16 = Float(16)
FLOAT32 = Float(32)
FLOAT64 = Float(64)
FLOAT80 = Float(80)
FLOAT128 = Float(128)

BOOL = Bool()
BIT = Bits(1)
INT = Integer()
REAL = Real()
VOID = Void()


_TYPE_CLASS = dict(s=Sint,
                   u=Uint,
                   b=Bits,
                   f=Float)
_TYPE_NMAP = dict(bit=BIT,
                  int=INT,
                  real=REAL,
                  bool=BOOL,
                  void=VOID)
_HAS_BITS = {Uint, Sint, Bits, Float}


def has_bits(tclass):
  return tclass in _HAS_BITS


def tclass_from_string(tcls):
  tclass = _TYPE_CLASS.get(tcls)
  if tclass is None:
    pyu.fatal(f'Unknown type class: {tcls}')

  return tclass


def dtype_from_string(s):
  # Accepted formats:
  #
  #   u32
  #   real
  #   u16(4, 4)
  #   f32(12)
  ls = s.lower()

  m = re.match(r'(' + '|'.join(_TYPE_CLASS.keys()) + r')(\d+)', ls)
  if m:
    dtype = _TYPE_CLASS[m.group(1)](int(m.group(2)))
    ls = ls[m.end(): ]
  else:
    m = re.match(r'(' + '|'.join(_TYPE_NMAP.keys()) + r')', ls)
    if m:
      dtype = _TYPE_NMAP[m.group(1)]
      ls = ls[m.end(): ]
    else:
      pyu.fatal(f'Unknown type string: {s}')

  m = re.match(r'\((\d+(,\d+)*)\)$', ls)
  if m:
    shape = tuple(int(x) for x in m.group(1).split(','))
  elif not ls:
    shape = None
  else:
    pyu.fatal(f'Unknown type string: {s}')

  return mkarray(dtype, *shape) if shape is not None else dtype


class TypeMatcher:

  def __init__(self, dtype=None, tclass=None):
    self.dtype = dtype
    self.tclass = tclass

  @classmethod
  def parse(cls, tmstr):
    dtype, tclass = None, None
    if tmstr != '*':
      m = re.match(r'(.+)\*$', tmstr)
      if m:
        tclass = tclass_from_string(m.group(1))
      else:
        dtype = dtype_from_string(tmstr)

    return cls(dtype=dtype, tclass=tclass)

  def check_value(self, arg, msg=''):
    if self.dtype is not None and self.dtype != arg.dtype:
      pyu.fatal(f'Mismatch type{msg}: {arg.dtype} vs. {self.dtype}')
    if self.tclass is not None and not isinstance(arg.dtype, self.tclass):
      pyu.fatal(f'Mismatch type class{msg}: {arg.dtype} vs. {pyiu.cname(self.tclass)}')


def mkarray(base_type, *shape):
  ashape = shape + base_type.full_shape

  return base_type.new_shape(*ashape)

