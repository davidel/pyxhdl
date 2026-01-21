import collections

import py_misc_utils.inspect_utils as pyiu
import py_misc_utils.utils as pyu

from .decorators import *
from .port import *
from .types import *
from .vars import *
from .utils import *


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

      self.args[pin.name] = ArgPort(arg, pin)

    for arg_name, arg in self.ARGS.items():
      self.kwargs[arg_name] = kwargs.get(arg_name, arg)

  def enum_processes(self):
    for name, func in self.__class__.__dict__.items():
      if is_hdl_function(func):
        if needs_self(func):
          func = getattr(self, name)

        yield func


def make_port_ref(pin):
  # The Ref constructor will assign the proper RO/RW mode according to the
  # vspec.const attribute.
  return Ref(pin.name, vspec=VSpec(const=pin.is_ro(), port=pin))


def verify_port_arg(pin, arg):
  if pin.type is not None:
    tmatch = TypeMatcher.parse(pin.type)
    tmatch.check_value(arg, msg=f' for entity port "{pin.name}"')

