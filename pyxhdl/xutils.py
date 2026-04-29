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
def gather(src, start, stop, step=1) -> Value:
  nstart, nstop = pycu.norm_slice(start, stop, src.dtype.shape[0])

  return gather2(src, range(nstart, nstop, step))


@hdl
def gather2(src, idxseq) -> Value:
  shape = list(src.dtype.shape)
  indices = tuple(idxseq)
  shape[0] = len(indices)

  result = mkwire(src.dtype.new_shape(*shape), name=_xname('gather'))
  for i, pos in enumerate(indices):
    result[i] = src[pos]

  return result
