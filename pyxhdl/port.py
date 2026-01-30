import re

import py_misc_utils.core_utils as pycu
import py_misc_utils.inspect_utils as pyiu
import py_misc_utils.module_utils as pymu
import py_misc_utils.utils as pyu

from .types import *
from .vars import *
from .utils import *


class Port:

  __slots__ = ('name', 'idir', 'type', 'default')

  IN = 'IN'
  OUT = 'OUT'
  INOUT = 'INOUT'
  IFC = 'IFC'

  def __init__(self, name, idir, type=None, default=None):
    self.name = name
    self.idir = idir
    self.type = type
    self.default = default

  def __repr__(self):
    rfmt = pyu.repr_fmt(self, 'name=,idir=,type,default')

    return f'{pyiu.cname(self)}({rfmt})'

  def __hash__(self):
    return hash((self.name, self.idir, self.type, self.default))

  def __eq__(self, other):
    return (self.name == other.name and self.idir == other.idir and
            self.type == other.type and self.default == other.default)

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

  def verify_arg(self, arg):
    if self.type is not None:
      if self.is_ifc():
        ifc_class, ifc_port = self.ifc_split()

        pcls, = pymu.import_module_names(ifc_class)

        if not isinstance(arg.origin, pcls):
          pyu.fatal(f'Invalid argument of type {pyiu.cname(arg.origin)} ' \
                    'when {ifc_class} is required')
      else:
        tmatch = TypeMatcher.parse(self.type)
        tmatch.check_value(arg, msg=f' for entity port "{self.name}"')

  @classmethod
  def parse(cls, pdecl):
    m = re.match(r'(=|\+|\*)?(\w+)(:([^\s]*))?(\s*=\s*(\w+))?$', pdecl)
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

    type_default = dtype_from_string(m.group(6)) if m.group(6) else None

    return cls(m.group(2), idir, type=m.group(4), default=type_default)

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
  match pin.idir:
    case Port.IN:
      mode = Ref.RO

    case Port.OUT:
      mode = Ref.WO

    case Port.INOUT:
      mode = Ref.RW

    case _:
      pyu.fatal(f'Unrecognized Port direction: {pin.idir}')

  return Ref(pin.name, mode=mode, vspec=VSpec(port=pin), vname=pin.name)

