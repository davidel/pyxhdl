import collections

import py_misc_utils.inspect_utils as pyiu
import py_misc_utils.utils as pyu

from .decorators import *
from .port import *
from .types import *
from .vars import *
from .utils import *


ArgPort = collections.namedtuple('ArgPort', 'arg, port')

POSEDGE = 'POSEDGE'
NEGEDGE = 'NEGEDGE'
LEVEL = 'LEVEL'

Sens = collections.namedtuple('Sens', 'trigger', defaults=[LEVEL])


class _CoreEntity:

  def __init_subclass__(cls):
    cls.PORTS = cls._get_ports(cls.PORTS)

  @classmethod
  def _get_ports(cls, cports):
    return Port.parse_list(cports)


class Entity(_CoreEntity):

  PORTS = tuple()
  ARGS = dict()
  NAME = None

  def __init__(self, **kwargs):
    super().__init__()
    self.args = dict()
    self.kwargs = dict()

    for pin in self.PORTS:
      arg = kwargs.get(pin.name)
      if arg is None:
        pyu.fatal(f'Missing argument "{pin.name}" for Entity "{pyiu.cname(self)}"')

      if pin.is_ifc():
        arg = pin.ifc_view(arg)

      self.args[pin.name] = ArgPort(arg, pin)

    for arg_name, arg in self.ARGS.items():
      self.kwargs[arg_name] = kwargs.get(arg_name, arg)

  def __repr__(self):
    gargs = self.kwargs.copy()
    gargs.update(self.args)

    rstr = pyu.stri(gargs)

    return pyiu.cname(self) + '(' + rstr[1: -1] + ')'

  def expanded_ports(self):
    xports = []
    for name, aport in self.args.items():
      if aport.port.is_ifc():
        for pin, arg in aport.port.ifc_expand(aport.arg):
          xports.append(ArgPort(arg, pin))
      else:
        xports.append(aport)

    return tuple(xports)

  def enum_processes(self):
    for name, func in self.__class__.__dict__.items():
      if is_hdl_function(func):
        if needs_self(func):
          func = getattr(self, name)

        yield func

