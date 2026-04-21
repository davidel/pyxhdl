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

  def __init__(self, name, **kwargs):
    from . import xlib

    self.name = name
    self._args = tuple(sorted(kwargs.keys()))
    self._fields = dict()
    self._xlib = xlib

    for k, v in kwargs.items():
      setattr(self, k, v)

  @property
  def origin(self):
    return getattr(self, 'origin_ifc', self)

  def _get_port(self, port_name):
    ports_spec = getattr(self, port_name, None)
    if ports_spec is None:
      fatal(f'Invalid port name: {port_name}')

    return Port.parse_list(ports_spec)

  def __hash__(self):
    hargs = [getattr(self, name) for name in self._args]

    for name in sorted(self._fields.keys()):
      value = getattr(self, name)
      if isinstance(value, Value):
        hargs.append((name, value.dtype))
      else:
        hargs.append((name, value))

    return hash(tuple(hargs))

  def __eq__(self, other):
    if self._args != other._args:
      return False

    if self._fields != other._fields:
      return False

    for name in self._args:
      if getattr(self, name) != getattr(other, name):
        return False

    for name in self._fields.keys():
      value, ovalue = getattr(self, name), getattr(other, name)
      if isinstance(value, Value):
        if value.dtype != ovalue.dtype:
          return False
      elif value != ovalue:
        return False

    return True

  def __repr__(self):
    parts = [f'{name}:{getattr(self, name)}' for name in self._args]

    for name in self._fields.keys():
      value = getattr(self, name)
      if isinstance(value, Value):
        parts.append(f'{name}:{value.dtype}')
      else:
        parts.append(f'{name}:{value}')

    return pyiu.cname(self) + '(' + ', '.join(parts) + ')'

  def _set_field(self, name, iname, ivalue):
    setattr(self, name, ivalue)
    self._fields[name] = iname


class InterfaceView(_InterfaceBase):

  def __init__(self, origin, name):
    super().__init__(name, **{k: getattr(origin, k) for k in origin._args})
    self.origin_ifc = origin

  def add_field(self, name, value, mode):
    if not isinstance(value, Value):
      fatal(f'Wrong field value type (should be Value): {value}')

    vref = value.ref
    if vref is None:
      fatal(f'Wrong field value type (should contain a Ref): {value}')

    xname = subname(self.name, name)

    vref = vref.new_mode(minor_mode(vref.mode, mode))
    vref = vref.new_name(xname, vname=xname)

    self._set_field(name, xname, value.new_value(vref))

  def add_view(self, name, value):
    self._set_field(name, name, value)


class Interface(_InterfaceBase):

  def __init__(self, name, **kwargs):
    args, fields = Interface._split_args(kwargs)

    super().__init__(name, **args)
    self._uname = self._xlib.generate_name(name, shortzero=True)
    for field_name, field_value in fields.items():
      self.mkfield(field_name, field_value)
    if fstr := getattr(self, 'FIELDS', None):
      self.create_fields(fstr)

  @staticmethod
  def _split_args(kwargs):
    args, fields = dict(), dict()
    for k, v in kwargs.items():
      if isinstance(v, (Value, Interface, Type)):
        fields[k] = v
      else:
        args[k] = v

    return args, fields

  def _mkvalue(self, name, dtype, init=None):
    vtype = dtype_from_string(dtype) if isinstance(dtype, str) else dtype

    if init is not None:
      return mkvreg(vtype, init, name=name)
    else:
      return mkreg(vtype, name=name)

  def mkfield(self, name, value, init=None):
    if isinstance(value, Value):
      if value.name is not None:
        xname, fvalue = value.name, value
      else:
        xname = subname(self._uname, name)
        if value.ref is None or value.ref.mode == Ref.RO:
          self._xlib.assign(xname, mkwire(value.dtype))

        self._xlib.assign(xname, value)
        fvalue = self._xlib.load(xname)
    elif isinstance(value, Interface):
      xname, fvalue = name, value
    else:
      xname = subname(self._uname, name)
      xvalue = self._mkvalue(xname, value, init=init)

      self._xlib.assign(xname, xvalue)
      fvalue = self._xlib.load(xname)

    self._set_field(name, xname, fvalue)

  def create_fields(self, fstr):
    for fs in pyu.comma_split(fstr):
      m = re.match(r'(\w+)\s*:\s*([^=]+)(\s*=\s*(.+))?', fs)
      if not m:
        fatal(f'Invalid field format: {fs}')

      name, ftype, fvalue = m.group(1), m.group(2), m.group(4)

      self.mkfield(name, ftype, init=pycu.infer_value(fvalue) if fvalue else None)

  @hdl
  def reset(self):
    pass

  def create_port_view(self, name, port_name):
    ports = self._get_port(port_name)

    view = InterfaceView(self, name)
    for pin in ports:
      value = getattr(self, pin.name)
      if isinstance(value, Interface):
        view.add_view(pin.name, pin.ifc_view(value))
      else:
        view.add_field(pin.name, value, pin.get_mode())

    return view

  def expand_port(self, name, port_name):
    ports = self._get_port(port_name)

    expanded = []
    for pin in ports:
      value = getattr(self, pin.name)
      if isinstance(value, Interface):
        expanded.extend(pin.ifc_expand(value))
      else:
        expanded.append((pycu.new_with(pin, name=subname(name, pin.name)), value))

    return tuple(expanded)

