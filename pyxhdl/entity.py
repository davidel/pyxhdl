import collections
import logging
import re

import py_misc_utils.utils as pyu

from .decorators import *
from .types import *
from .vars import *
from .utils import *


IN = 1
OUT = 2
INOUT = 3
IO_NAME = {
  IN: 'IN',
  OUT: 'OUT',
  INOUT: 'INOUT',
}

Port = collections.namedtuple('Port', 'name, idir, type', defaults=[None])

ArgPort = collections.namedtuple('ArgPort', 'arg, port')

POSEDGE = 1
NEGEDGE = 2
LEVEL = 3
TRIG_NAME = {
  POSEDGE: 'POSEDGE',
  NEGEDGE: 'NEGEDGE',
  LEVEL: 'LEVEL',
}

Sens = collections.namedtuple('Sens', 'trigger', defaults=[LEVEL])


class _CoreEntity(object):

  def __init_subclass__(cls):
    cls.PORTS = cls._get_ports(cls.PORTS)

  @classmethod
  def _get_ports(cls, cports):
    if isinstance(cports, tuple):
      return cports
    elif isinstance(cports, list):
      return tuple(cports)
    elif isinstance(cports, str):
      ports = []
      for pdecl in pyu.resplit(cports, ','):
        sport, *pargs = pyu.resplit(pdecl, ':')

        m = re.match(r'(=|\+)?(\w+)$', sport)
        if not m:
          pyu.fatal(f'Unrecognized port format: {sport}')

        idir = OUT if m.group(1) == '=' else INOUT if m.group(1) == '+' else IN

        ptype = pargs[0] if len(pargs) > 0 else None

        ports.append(Port(name=m.group(2), idir=idir, type=ptype))

      return tuple(ports)
    else:
      pyu.fatal(f'Unrecognized PORTS value: {cports}')


class Entity(_CoreEntity):

  PORTS = tuple()
  ARGS = dict()
  NAME = None

  def __init__(self, **kwargs):
    super().__init__()
    self._args = dict()
    self._kwargs = dict()

    for pin in self.PORTS:
      arg = kwargs.get(pin.name, None)
      if arg is None:
        pyu.fatal(f'Missing argument "{pin.name}" for Entity "{cname(self)}"')

      self._args[pin.name] = ArgPort(arg, pin)

    for arg_name, arg in self.ARGS.items():
      self._kwargs[arg_name] = kwargs.get(arg_name, arg)

  @property
  def args(self):
    return self._args

  @property
  def kwargs(self):
    return self._kwargs

  def enum_processes(self):
    for name, func in self.__class__.__dict__.items():
      if is_hdl_function(func):
        if needs_self(func):
          func = getattr(self, name)

        yield func


def make_port_ref(pin):
  vspec = VSpec(const=pin.idir == IN, port=pin)

  return Ref(pin.name, mode=Ref.RO, vspec=vspec) if pin.idir == IN else Ref(pin.name, vspec=vspec)


def verify_port_arg(pin, arg):
  if pin.type is not None:
    tmatch = TypeMatcher.parse(pin.type)
    tmatch.check_value(arg, msg=f' for entity port "{pin.name}"')

