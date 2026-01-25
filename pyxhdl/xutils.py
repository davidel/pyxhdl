from .decorators import *
from .emitter import *
from .pyxhdl import *
from .types import *
from .vars import *
from .utils import *


@hdl
def bit_swap(src):
  ctx = CodeGen.current()

  dest = mkwire(src.dtype, name=ctx.generate_name('bit_swap'))
  for i in range(dest.dtype.nbits):
    dest[i] = src[dest.dtype.nbits - 1 - i]

  return dest

