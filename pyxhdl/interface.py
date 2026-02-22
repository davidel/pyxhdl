import re
import yaml

import py_misc_utils.core_utils as pycu
import py_misc_utils.inspect_utils as pyiu
import py_misc_utils.utils as pyu

from .decorators import *
from .port import *
from .types import *
from .vars import *
from .utils import *


class _InterfaceBase:

  def __init__(self, name, **kwargs):
    from . import xlib

    self.name = name
    self.args = tuple(sorted(kwargs.keys()))
    self.fields = dict()
    self.xlib = xlib

    for k, v in kwargs.items():
      setattr(self, k, v)

  @property
  def origin(self):
    return getattr(self, 'origin_ifc', self)

  def __hash__(self):
    hargs = tuple((getattr(self, name) for name in self.args))
    hfields = tuple((name, getattr(self, name).dtype) for name in
                    sorted(self.fields.keys()))

    return hash(hargs + hfields)

  def __eq__(self, other):
    if self.args != other.args:
      return False

    if self.fields != other.fields:
      return False

    for name in self.args:
      if getattr(self, name) != getattr(other, name):
        return False

    for name in self.fields.keys():
      if getattr(self, name).dtype != getattr(other, name).dtype:
        return False

    return True

  def __repr__(self):
    parts = [f'{name}:{getattr(self, name)}' for name in self.args]
    parts += [f'{name}:{getattr(self, name).dtype}' for name in self.fields.keys()]

    return pyiu.cname(self) + '(' + ', '.join(parts) + ')'


class InterfaceView(_InterfaceBase):

  def __init__(self, origin, name):
    super().__init__(name, **{k: getattr(origin, k) for k in origin.args})
    self.origin_ifc = origin

  def add_field(self, name, value, mode):
    if not isinstance(value, Value):
      fatal(f'Wrong field value type (should be Value): {value}')

    vref = value.ref
    if vref is None:
      fatal(f'Wrong field value type (should contain a Ref): {value}')

    xname = subname(self.name, name)

    vref = vref.new_mode(vref.mode if vref.mode == Ref.RO else mode)
    vref = vref.new_name(xname, vname=xname)

    xvalue = value.new_value(vref)

    setattr(self, name, xvalue)

    self.fields[name] = xname


class Interface(_InterfaceBase):

  def __init__(self, name, **kwargs):
    super().__init__(name, **kwargs)
    self._uname = self.xlib.generate_name(name, shortzero=True)
    if fstr := getattr(self, 'FIELDS', None):
      self.create_fields(fstr)

  def _mkvalue(self, name, value, init=None):
    if isinstance(value, Type):
      if init is not None:
        return mkvreg(value, init, name=name)
      else:
        return mkreg(value, name=name)
    elif isinstance(value, str):
      if init is not None:
        return mkvreg(dtype_from_string(value), init, name=name)
      else:
        return mkreg(dtype_from_string(value), name=name)
    else:
      fatal(f'Invalid interface value: {value}')

  def mkfield(self, name, value, init=None):
    if isinstance(value, Value):
      if value.name is not None:
        xname, fvalue = value.name, value
      else:
        xname, fvalue = subname(self._uname, name), value

        self.xlib.assign(xname, fvalue)
    else:
      xname = subname(self._uname, name)
      fvalue = self._mkvalue(xname, value, init=init)

      self.xlib.assign(xname, fvalue)

    setattr(self, name, self.xlib.load(xname))

    self.fields[name] = xname

  def create_fields(self, fstr):
    for fs in pyu.comma_split(fstr):
      name, fvtype = re.split(r'\s*:\s*', fs, maxsplit=1)
      ftype, *fvalue = re.split(r'\s*=\s*', fvtype, maxsplit=1)

      self.mkfield(name, ftype, init=yaml.safe_load(fvalue[0]) if fvalue else None)

  @hdl
  def reset(self):
    pass

  def create_port_view(self, name, port_name):
    ports_spec = getattr(self, port_name, None)
    if ports_spec is None:
      fatal(f'Invalid port name: {port_name}')

    ports = Port.parse_list(ports_spec)

    view = InterfaceView(self, name)
    for pin in ports:
      mode = Ref.RO if pin.idir == Port.IN else Ref.RW

      view.add_field(pin.name, getattr(self, pin.name), mode)

    return view

  def expand_port(self, name, port_name):
    ports_spec = getattr(self, port_name, None)
    if ports_spec is None:
      fatal(f'Invalid port name: {port_name}')

    ports = Port.parse_list(ports_spec)
    expanded = []
    for pin in ports:
      expanded.append((pycu.new_with(pin, name=subname(name, pin.name)),
                       getattr(self, pin.name)))

    return tuple(expanded)

