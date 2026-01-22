import re

import py_misc_utils.utils as pyu

from .types import *
from .vars import *
from .utils import *


class Port:

  __slots__ = ('name', 'idir', 'type')

  IN = 'IN'
  OUT = 'OUT'
  INOUT = 'INOUT'

  def __init__(self, name, idir, type=None):
    self.name = name
    self.idir = idir
    self.type = type

  def __repr__(self):
    rfmt = pyu.repr_fmt(self, 'name=,idir=,type')

    return f'{pyiu.cname(self)}({rfmt})'

  def __hash__(self):
    return hash((self.name, self.idir, self.type))

  def __eq__(self, other):
    return (self.name == other.name and self.idir == other.idir and
            self.type == other.type)

  def is_ro(self):
    return self.idir == self.IN

  def is_wo(self):
    return self.idir == self.OUT

  def is_rd(self):
    return self.idir in (self.IN, self.INOUT)

  def is_wr(self):
    return self.idir in (self.OUT, self.INOUT)

  def is_rw(self):
    return self.idir == self.INOUT

  @classmethod
  def parse(cls, pdecl):
    sport, *pargs = pyu.resplit(pdecl, ':')

    m = re.match(r'(=|\+)?(\w+)$', sport)
    if not m:
      pyu.fatal(f'Unrecognized port format: {sport}')

    idir = cls.OUT if m.group(1) == '=' else cls.INOUT if m.group(1) == '+' else cls.IN

    ptype = pargs[0] if len(pargs) > 0 else None

    return cls(m.group(2), idir, type=ptype)

  @classmethod
  def parse_list(cls, cports):
    if isinstance(cports, (list, tuple)):
      if not all(isinstance(p, cls) for p in cports):
        pyu.fatal(f'Unrecognized port value: {cports}')

      return tuple(cports)
    elif isinstance(cports, str):
      ports = []
      for pdecl in pyu.resplit(cports, ','):
        ports.append(cls.parse(pdecl))

      return tuple(ports)
    else:
      pyu.fatal(f'Unrecognized ports value: {cports}')


def make_port_ref(pin):
  # The Ref constructor will assign the proper RO/RW mode according to the
  # vspec.const attribute.
  return Ref(pin.name, vspec=VSpec(const=pin.is_ro(), port=pin))


def verify_port_arg(pin, arg):
  if pin.type is not None:
    tmatch = TypeMatcher.parse(pin.type)
    tmatch.check_value(arg, msg=f' for entity port "{pin.name}"')

