import py_misc_utils.num_utils as pynu

import pyxhdl as X
from pyxhdl import xlib as XL


class FirstBitSet(X.Entity):

  PORTS = 'DATA, =BITIDX'

  @X.hdl_process(sens='DATA')
  def run():
    nbits = max(DATA.dtype.nbits // 8, 4)
    nparts = (DATA.dtype.nbits + nbits - 1) // nbits

    found = X.mkwire(X.Bits(nparts))
    indices = X.mkwire(X.mkarray(BITIDX.dtype, nparts))

    found = 0
    indices = -1
    BITIDX = -1

    for i in range(nparts):
      part_size = min(nbits, DATA.dtype.nbits - i * nbits)
      mask = ((1 << part_size) - 1) << (i * nbits)

      if (DATA & mask) != 0:
        with XL.loop_mode_hdl():
          for j in range(part_size):
            if DATA[i * nbits + j] == 1:
              indices[i] = i * nbits + j
              found[i] = 1
              break

    with XL.loop_mode_hdl():
      for i in range(nparts):
        if found[i] == 1:
          BITIDX = indices[i]
          break


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

