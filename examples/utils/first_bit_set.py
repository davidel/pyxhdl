import py_misc_utils.num_utils as pynu

import pyxhdl as X
from pyxhdl import xlib as XL


class FirstBitSet(X.Entity):

  PORTS = 'DATA, =BITIDX'

  @X.hdl_process(sens='DATA')
  def run():
    nbits = max(DATA.dtype.nbits // 8, 4)
    nparts = int(DATA.dtype.nbits / nbits)

    BITIDX = -1

    for i in range(nparts):
      part_size = min(nbits, DATA.dtype.nbits - i * nbits)
      mask = ((1 << part_size) - 1) << (i * nbits)

      if (DATA & mask) != 0:
        found = X.mkwire(X.BIT, name=f'found_{i}')
        found = 0

        for j in range(part_size):
          if found == 0 and DATA[i * nbits + j] == 1:
            BITIDX = i * nbits + j
            found = 1

        del found


class Test(X.Entity):

  ARGS = dict(num_tests=20,
              width=32) | FirstBitSet.ARGS

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    DATA = X.mkreg(X.Bits(width))
    BITIDX = X.mkreg(X.Sint(width.bit_length()))

    FirstBitSet(DATA=DATA,
                BITIDX=BITIDX,
                **{k: locals()[k] for k in FirstBitSet.ARGS.keys()})

  @X.hdl_process()
  def run(self):
    import random

    from pyxhdl import testbench as TB

    for i in range(num_tests):
      data = random.randint(0, 2**width - 1)
      nbit = random.randint(0, width - 1)
      if nbit != 0:
        data &= ~((1 << nbit) - 1)

      data |= 1 << nbit

      DATA = data

      XL.wait_for(1e-9)

      TB.compare_value(BITIDX, nbit, msg=f' : data={data:b}')

    XL.finish()

