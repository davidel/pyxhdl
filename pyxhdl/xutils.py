from .decorators import *
from .emitter import *
from .pyxhdl import *
from .types import *
from .utils import *
from .vars import *
from . import xlib as XL


@hdl
def bit_swap(src):
  dest = mkwire(src.dtype, name=XL.generate_name('bit_swap'))
  for i in range(dest.dtype.nbits):
    dest[i] = src[dest.dtype.nbits - 1 - i]

  return dest

