import logging
import re

import py_misc_utils.utils as pyu

from .pyxhdl import *
from .types import *
from .vars import *


def argn_dtype(n):
  def typefn(args):
    return args[n].dtype

  return typefn


def create_function(fnname, fnmap, fnsig=None, dtype=None):
  return _ExternalFunction(fnname, fnmap, fnsig=fnsig, dtype=dtype)


class _Marshal(object):

  BITS_CLASSES = {Uint, Sint, Bits}

  def __init__(self, mstr, fnname, argno):
    self._fnname = fnname
    self._argno = argno
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
          pyu.fatal(f'Wrong type for argument {self._argno} of {self._fnname}() ' \
                    f'call: {pyu.cname(tclass)} vs {pyu.cname(arg.dtype)}')
      else:
        arg = ctx.emitter.cast(arg, dtype)
    else:
      arg = ctx.emitter.tclass_cast(tclass, arg)

    return arg

  def __call__(self, ctx, arg):
    if self._tmatch.dtype is not None:
      return ctx.emitter.cast(arg, self._tmatch.dtype)
    if self._tmatch.tclass is not None:
      return self._tclass_cast(ctx, arg, self._tmatch.tclass)

    return arg


class _ExternalFunction(object):

  def __init__(self, fnname, fnmap, fnsig=None, dtype=None):
    marshals = []
    if fnsig:
      for sarg in pyu.strip_split(fnsig, ','):
        marshals.append(_Marshal(sarg, fnname, len(marshals)))

    self._fnname = fnname
    self._fnmap = fnmap
    self._marshals = tuple(marshals)
    self._dtype = dtype
    # PyXHDL looks for __name__ to emit debug logging when running AST function calls.
    self.__name__ = fnname

  def __call__(self, *args):
    ctx = CodeGen.current()

    cargs = []
    for i, arg in enumerate(args):
      if i < len(self._marshals):
        arg = self._marshals[i](ctx, arg)

      cargs.append(arg)

    # It is possible to make function lookup depend not only on backend, but on inputs
    # signature. But since VHDL (which is my main target ATM) supports function overloading,
    # this can be handled within the VHDL library functions supplied with PyXHDL.
    fmap = self._fnmap.get(ctx.emitter.kind, None)
    if fmap is None:
      pyu.fatal(f'Unable to resolve function {self._fnname}() for {ctx.emitter.kind} backend')

    if callable(fmap):
      fnname = fmap(ctx, cargs)
    else:
      fnname = fmap

    dtype = self._dtype(cargs) if callable(self._dtype) else self._dtype

    return ctx.emit_call(fnname, cargs, dtype)

