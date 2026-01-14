# Cannot depend of local modules!
import collections
import copy
import inspect
import os
import re
import sys
import textwrap

import py_misc_utils.context_managers as pycm
import py_misc_utils.core_utils as pycu
import py_misc_utils.utils as pyu


_FuncInfo = collections.namedtuple('FuncInfo', 'filename, lineno, source')

NONE = object()


def get_obj_globals(obj, defval=None):
  mod = getattr(obj, '__module__', None)
  if mod is not None:
    imod = sys.modules.get(mod)
    if imod is not None:
      return imod.__dict__

  return getattr(obj, '__globals__', defval)


def create_globals(obj, source_globals=None):
  obj_globs = get_obj_globals(obj, defval=dict())
  if source_globals:
    gglobals = copy.copy(source_globals)
    for k, v in pycu.enum_values(obj_globs):
      if not k.startswith('__'):
        gglobals[k] = v
  else:
    gglobals = {k: v for k, v in pycu.enum_values(obj_globs)}

  return gglobals


def fetch_attr(obj, name):
  return obj.get(name, NONE) if isinstance(obj, dict) else getattr(obj, name, NONE)


def vload(name, globs, locs):
  v = fetch_attr(locs, name)
  if v is NONE:
    v = fetch_attr(globs, name)
    if v is NONE:
      bins = globs.get('__builtins__')
      if bins is not None:
        v = fetch_attr(bins, name)

  return v


# Do not add "'" as this needs not to be parenthesized in SystemVerilog.
_BOUNDS = {
  '{': '}',
  '(': ')',
  '[': ']',
  '"': '"',
}
_NEEDSPAR_RX = re.compile(r'[ +\-*/%!~&|^]')

def paren(sx):
  level, levch, skip = 0, [None], False
  for c in sx:
    if skip:
      skip = False
    elif c == '\\':
      skip = True
    elif c == levch[-1]:
      levch.pop()
      level -= 1
    elif c in _BOUNDS:
      levch.append(_BOUNDS[c])
      level += 1
    elif level == 0 and _NEEDSPAR_RX.match(c):
      return f'({sx})'

  return sx


_FN_INFO = '__fninfo__'

def get_function_info(func):
  fninfo = getattr(func, _FN_INFO, None)
  if fninfo is None:
    filename = inspect.getsourcefile(func)
    slines, lineno = inspect.getsourcelines(func)
    source = textwrap.dedent(''.join(slines))

    fninfo = _FuncInfo(filename=filename, lineno=lineno, source=source)

  return fninfo


def set_function_info(func, filename, lineno, source):
  setattr(func, _FN_INFO, _FuncInfo(filename=filename, lineno=lineno, source=source))


def needs_self(func):
  sig = inspect.signature(func)
  if sig.parameters:
    name, param = next(iter(sig.parameters.items()))

    return name == 'self'

  return False


def flat2shape(parts, shape, opar, cpar):
  sparts = parts
  for dim in reversed(shape):
    elist = [sparts[x: x + dim] for x in range(0, len(sparts), dim)]
    sparts = [opar + ', '.join(l) + cpar for l in elist]

  return sparts[0]


class _EntityRecord:

  def __init__(self, eclass, pargs, kwargs):
    self.eclass = eclass
    self.pargs = pargs
    self.kwargs = kwargs
    self.hash = pycu.genhash((eclass, pargs, kwargs))

  def __hash__(self):
    return self.hash

  def __eq__(self, other):
    return (self.eclass == other.eclass and self.kwargs == other.kwargs and
            self.pargs == other.pargs)


class EntityVersions:

  def __init__(self):
    self._versions = collections.defaultdict(dict)

  def getname(self, eclass, pargs, kwargs):
    erec = _EntityRecord(eclass, pargs, kwargs)

    ent_name = eclass.__name__
    eldict = self._versions[ent_name]
    ver = eldict.get(erec)
    if ver is None:
      ver = len(eldict)
      eldict[erec] = ver

    return ent_name if ver == 0 else f'{ent_name}_{ver}', erec


def temp_attributes(obj, **attrs):
  saved = dict()

  def infn():
    for k, v in attrs.items():
      saved[k] = getattr(obj, k, NONE)
      setattr(obj, k, v)

    return obj

  def outfn(*exc):
    for k, v in saved.items():
      if v is NONE:
        delattr(obj, k)
      else:
        setattr(obj, k, v)

    return False

  return pycm.CtxManager(infn, outfn)

