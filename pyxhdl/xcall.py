import re

import py_misc_utils.alog as alog
import py_misc_utils.inspect_utils as pyiu
import py_misc_utils.utils as pyu

from .pyxhdl import *
from .types import *
from .utils import *
from .vars import *


def argn_dtype(n):
  def typefn(args, kwargs):
    return args[n].dtype

  return typefn


def create_function(fnname, fnmap, fnsig=None, dtype=None):
  return _ExternalFunction(fnname, fnmap, fnsig=fnsig, dtype=dtype)


class _Marshal:

  BITS_CLASSES = {Uint, Sint, Bits}

  def __init__(self, mstr, fnname, argref):
    self._fnname = fnname
    self._argref = argref
    self._tmatch = TypeMatcher.parse(mstr)

  def _get_tclass_dtype(self, tclass, dtype):
    if not has_bits(tclass):
      return tclass()
    if tclass in self.BITS_CLASSES and type(dtype) in self.BITS_CLASSES:
      return tclass(dtype.nbits)

  def _tclass_cast(self, ctx, arg, tclass):
    if isinstance(arg, Value):
      dtype = self._get_tclass_dtype(tclass, arg.dtype)
      if dtype is None:
        if not isinstance(arg.dtype, tclass):
          fatal(f'Wrong type for argument {self._argref} of {self._fnname}() ' \
                f'call: {pyiu.cname(tclass)} vs {pyiu.cname(arg.dtype)}')
      else:
        arg = ctx.emitter.cast(arg, dtype)
    else:
      arg = ctx.emitter.tclass_cast(tclass, arg)

    return arg

  def __call__(self, ctx, arg):
    return self._tmatch.cast(
      arg,
      dtype_fn=lambda v, t: ctx.emitter.cast(v, t),
      tclass_fn=lambda v, t: self._tclass_cast(ctx, v, t))


class _ExternalFunction:

  def __init__(self, fnname, fnmap, fnsig=None, dtype=None):
    marshals, kwmarshals = [], dict()
    if fnsig:
      for sarg in pyu.resplit(fnsig, ','):
        if m := re.match(r'\s*(\w+)\s*=\s*([^\s]+)', sarg):
          kwmarshals[m.group(1)] = _Marshal(m.group(2), fnname, m.group(1))
        else:
          marshals.append(_Marshal(sarg, fnname, len(marshals)))

    self._fnname = fnname
    self._fnmap = fnmap
    self._marshals = marshals
    self._kwmarshals = kwmarshals
    self._dtype = dtype
    # PyXHDL looks for __name__ to emit debug logging when running AST function calls.
    self.__name__ = fnname

  def __call__(self, *args, **kwargs):
    ctx = CodeGen.current()

    cargs = []
    for i, arg in enumerate(args):
      if i < len(self._marshals):
        arg = self._marshals[i](ctx, arg)

      cargs.append(arg)

    ckwargs = dict()
    for name, arg in kwargs.items():
      marshal = self._kwmarshals.get(name)
      if marshal is not None:
        arg = marshal(ctx, arg)

      ckwargs[name] = arg

    if isinstance(self._fnmap, dict):
      fmap = self._fnmap.get(ctx.emitter.kind)
      if fmap is None:
        fatal(f'Unable to resolve function {self._fnname}() for {ctx.emitter.kind} backend')
    else:
      fmap = self._fnmap

    dtype = self._dtype(cargs, ckwargs) if callable(self._dtype) else self._dtype

    if callable(fmap):
      call = fmap(ctx, cargs, ckwargs)

      return Value(dtype, call)
    else:
      if ckwargs:
        alog.warning(f'Keyword argument ignored for {self._fnname}() call: {ckwargs}')

      return ctx.emit_call(fmap, cargs, dtype)

