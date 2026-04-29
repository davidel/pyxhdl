import py_misc_utils.core_utils as pycu

from .decorators import *
from .emitter import *
from .pyxhdl import *
from .types import *
from .utils import *
from .vars import *
from . import xlib as XL


def _xname(base):
  return XL.generate_name(f'XU_{base}')


@hdl
def snap(value) -> Value:
  svalue = mkwire(value.dtype, name=_xname('snap'))

  svalue = value

  return svalue


@hdl
def bit_swap(src) -> Value:
  result = mkwire(src.dtype, name=_xname('bit_swap'))
  for i in range(result.dtype.nbits):
    result[i] = src[result.dtype.nbits - 1 - i]

  return result


@hdl
def gather(src, idxseq) -> Value:
  indices = tuple(idxseq)
  shape = (len(indices),) + src.dtype.shape[1: ]

  result = mkwire(src.dtype.new_shape(*shape), name=_xname('gather'))
  for i, pos in enumerate(indices):
    result[i] = src[pos]

  return result
