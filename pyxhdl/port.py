import re

import py_misc_utils.core_utils as pycu
import py_misc_utils.inspect_utils as pyiu
import py_misc_utils.module_utils as pymu
import py_misc_utils.utils as pyu

from .types import *
from .vars import *
from .utils import *


class Port:

  __slots__ = ('name', 'idir', 'type')

  IN = 'IN'
  OUT = 'OUT'
  INOUT = 'INOUT'
  IFC = 'IFC'

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

  def is_ifc(self):
    return self.idir == self.IFC

  def ifc_split(self):
    ifc_class, ifc_port = pycu.separate(self.type, '.', reverse=True)

    return ifc_class, ifc_port

  def ifc_view(self, value):
    ifc_class, ifc_port = self.ifc_split()

    return value.origin.create_port_view(self.name, ifc_port)

  def ifc_expand(self, value):
    ifc_class, ifc_port = self.ifc_split()

    return value.origin.expand_port(self.name, ifc_port)

  def ifc_field_name(self, fname):
    return subname(self.name, fname)

  @classmethod
  def parse(cls, pdecl):
    m = re.match(r'(=|\+|\*)?(\w+)(:([^\s]*))?$', pdecl)
    if not m:
      pyu.fatal(f'Unrecognized port format: {pdecl}')

    match m.group(1):
      case '=':
        idir = cls.OUT
      case '+':
        idir = cls.INOUT
      case '*':
        idir = cls.IFC
      case _:
        idir = cls.IN

    ptype = m.group(4)

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
    if pin.is_ifc():
      ifc_class, ifc_port = pin.ifc_split()

      pcls, = pymu.import_module_names(ifc_class)

      if not isinstance(arg.origin, pcls):
        pyu.fatal(f'Invalid argument of type {pyiu.cname(arg.origin)} when {ifc_class} is required')
    else:
      tmatch = TypeMatcher.parse(pin.type)
      tmatch.check_value(arg, msg=f' for entity port "{pin.name}"')

