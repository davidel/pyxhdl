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
def select(src, idxseq) -> Value:
  indices = tuple(idxseq)
  if not indices:
    fatal(f'Empty index set', exc=ValueError)

  shape = (len(indices),) + src.dtype.shape[1: ]

  result = mkwire(src.dtype.new_shape(*shape), name=_xname('select'))
  for i, pos in enumerate(indices):
    result[i] = src[pos]

  return result


@hdl
def split(src, *sizes, base=0) -> tuple[Value]:
  tsize = base + sum(sizes)
  if tsize > src.dtype.shape[0]:
    fatal(f'Cannot split {sizes} with base {base} from a source shape {src.dtype.shape}',
          exc=ValueError)

  values, pos = [], base
  for size in sizes:
    shape = (size,) + src.dtype.shape[1: ]
    svalue = mkwire(src.dtype.new_shape(*shape), name=_xname('split'))

    svalue = src[pos: pos + size]
    values.append(svalue)

    del svalue

    pos += size

  return tuple(values)

