import py_misc_utils.num_utils as pynu

import pyxhdl as X
from pyxhdl import xlib as XL


class FirstBitSet(X.Entity):

  PORTS = 'DATA, =BITIDX'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def run():
    FSTAGE = X.mkwire(X.mkarray(X.Sint(DATA.dtype.nbits.bit_length() + 1),
                                DATA.dtype.nbits + 1))

    FSTAGE[DATA.dtype.nbits] = -1
    for i in range(DATA.dtype.nbits - 1, -1, -1):
      FSTAGE[i] = i if DATA[i] == 1 else FSTAGE[i + 1]

    BITIDX = FSTAGE[0]


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
      ref_result = pynu.ffs(data, width)

      DATA = data

      XL.wait_for(1e-9)

      TB.compare_value(BITIDX, ref_result, msg=f' : data={data}')

    XL.finish()

