import re

import py_misc_utils.core_utils as pycu
import py_misc_utils.inspect_utils as pyiu
import py_misc_utils.utils as pyu

from .decorators import *
from .port import *
from .types import *
from .vars import *
from .utils import *


class _InterfaceBase:

  def __init__(self, name):
    self.name = name
    self.fields = dict()
    self.xlib = lazy_import('xlib')

  @property
  def origin(self):
    return getattr(self, 'origin_ifc', self)

  def __hash__(self):
    return hash(tuple((name, getattr(self, name).dtype) for name in self.fields.keys()))

  def __eq__(self, other):
    if self.fields != other.fields:
      return False

    for name in self.fields.keys():
      if getattr(self, name).dtype != getattr(other, name).dtype:
        return False

    return True

  def __repr__(self):
    parts = [f'{name}:{getattr(self, name).dtype}' for name in self.fields.keys()]

    return pyiu.cname(self) + '(' + ', '.join(parts) + ')'


class InterfaceView(_InterfaceBase):

  def __init__(self, origin, name):
    super().__init__(name)
    self.origin_ifc = origin

  def add_field(self, name, value, mode):
    if not isinstance(value, Value):
      pyu.fatal(f'Wrong field value type (should be Value): {value}')

    vref = value.ref
    if vref is None:
      pyu.fatal(f'Wrong field value type (should contain a Ref): {value}')

    xname = subname(self.name, name)

    vref = vref.new_mode(vref.mode if vref.mode == Ref.RO else mode)
    vref = vref.new_name(xname, vname=xname)

    xvalue = value.new_value(vref)

    setattr(self, name, xvalue)

    self.fields[name] = xname


class Interface(_InterfaceBase):

  _REVGEN = pycu.RevGen(fmt='{name}{ver}')

  def __init__(self, name):
    super().__init__(name)
    self._uname = self._REVGEN.newname(name, shortzero=True)
    if fstr := getattr(self, 'FIELDS', None):
      self.create_fields(fstr)

  def _mkvalue(self, name, value, init=None):
    if not isinstance(value, Value):
      if isinstance(value, Type):
        return mkreg(value, name=name)
      elif isinstance(value, str):
        if init:
          return mkvreg(dtype_from_string(value), init, name=name)
        else:
          return mkreg(dtype_from_string(value), name=name)
      else:
        pyu.fatal(f'Invalid interface value: {value}')

    return value

  def mkfield(self, name, value, init=None):
    xname = self.get_xname(name)

    fvalue = self._mkvalue(xname, value, init=init)

    self.xlib.assign(xname, fvalue)
    setattr(self, name, self.xlib.load(xname))

    self.fields[name] = xname

  def create_fields(self, fstr):
    for fs in pyu.comma_split(fstr):
      name, fvtype = re.split(r'\s*:\s*', fs, maxsplit=1)
      ftype, *fvalue = re.split(r'\s*=\s*', fvtype, maxsplit=1)

      self.mkfield(name, ftype, init=fvalue[0] if fvalue else None)

  def get_name(self, xname):
    if not xname.startswith(self._uname):
      pyu.fatal(f'Invalid external name: {xname}')

    return xname[len(self._uname) + 1: ]

  def get_xname(self, name):
    return subname(self._uname, name)

  @hdl
  def reset(self):
    pass

  def create_port_view(self, name, port_name):
    ports_spec = getattr(self, port_name, None)
    if ports_spec is None:
      pyu.fatal(f'Invalid port name: {port_name}')

    ports = Port.parse_list(ports_spec)

    view = InterfaceView(self, name)
    for pin in ports:
      mode = Ref.RO if pin.idir == Port.IN else Ref.RW

      view.add_field(pin.name, getattr(self, pin.name), mode)

    return view

  def expand_port(self, name, port_name):
    ports_spec = getattr(self, port_name, None)
    if ports_spec is None:
      pyu.fatal(f'Invalid port name: {port_name}')

    ports = Port.parse_list(ports_spec)
    expanded = []
    for pin in ports:
      expanded.append((pycu.new_with(pin, name=subname(name, pin.name)),
                       getattr(self, pin.name)))

    return tuple(expanded)

  def unpack(self, *names):
    udata = []
    for name in pyu.expand_strings(*names):
      udata.append(self.xlib.load(self.get_xname(name)))

    return udata if len(udata) != 1 else udata[0]

