import py_misc_utils.alog as alog
import py_misc_utils.core_utils as pycu
import py_misc_utils.utils as pyu

from .utils import *


class ExternLogic:

  def __init__(self, modname,
               funcname=None,
               nargs=None,
               params=None,
               args=None,
               name_remap=None,
               filename=None):
    self.modname = modname
    self.funcname = funcname
    self.nargs = nargs or 0
    self.params = params or ()
    self.args = args or dict()
    self.name_remap = name_remap or dict()
    self.filename = filename or modname


class ExternModule:

  def __init__(self, name):
    self.name = name
    self._logic = dict()

  def add_logic(self, name, logic):
    self._logic[name] = logic

  def get_logic(self, name):
    xlogic = self._logic.get(name)
    if xlogic is None:
      fatal(f'Unable to find {name} logic within {self.name} module')

    return xlogic

  @classmethod
  def load(cls, path):
    mdata = pyu.load_config(path)

    xmod = cls(mdata['name'])

    name_remap = mdata.get('name_remap')

    for fname in mdata.get('functions', []):
      fdata = mdata['functions'][fname]

      xlogic = pycu.obj_from_dict(ExternLogic, fdata)
      if not xlogic.name_remap and name_remap:
        xlogic.name_remap = name_remap

      xmod.add_logic(fname, xlogic)

    return xmod

