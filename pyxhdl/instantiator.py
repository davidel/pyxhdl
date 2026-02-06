import re

import py_misc_utils.core_utils as pycu


class _Instance:

  def __init__(self, name, params, args):
    self.name = name
    self.params = params
    self.args = args
    self.hash = pycu.genhash((name, params, args))

  def __hash__(self):
    return self.hash

  def __eq__(self, other):
    return (self.name == other.name and self.params == other.params and
            self.args == other.args)


class Instanciator:

  def __init__(self, param_key=None, revbase=None):
    self._param_key = param_key
    self._instances = dict()
    self._revgen = pycu.RevGen(revbase=revbase if revbase is not None else 1)

  def _cname(self, name):
    cname = re.sub(r'\W+', '_', name)

    return cname

  def getid(self, name, kwargs, force_new=False):
    params = kwargs.pop(self._param_key, dict()) if self._param_key else dict()
    inst = _Instance(name, params, kwargs)
    iid = self._instances.get(inst) if not force_new else None
    if iid is None:
      cname = self._cname(name)
      iid = self._revgen.newname(cname)

      self._instances[inst] = iid

    return iid

  def __iter__(self):
    for inst, iid in self._instances.items():
      yield iid, inst

