import pyxhdl as X
from pyxhdl import xlib as XL


class Switcher(X.Entity):

  PORTS = 'SEL, DIN, =SEL_DOUT, SEL_DIN, =DOUT'

  @X.hdl_process(proc_mode='comb')
  def switch():
    N = SEL_DIN.dtype.array_shape[0]

    SEL_DOUT = X.bitfill('X', SEL_DOUT.dtype.nbits)
    DOUT = X.bitfill('X', DOUT.dtype.nbits)

    for i in range(N):
      if SEL == i:
        SEL_DOUT[i] = DIN
        DOUT = SEL_DIN[i]


class Test(X.Entity):

  ARGS = dict(num_tests=20,
              num_channels=8,
              width=8) | Switcher.ARGS

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    SEL = X.mkreg(X.Uint(num_channels.bit_length()))
    DIN = X.mkreg(X.Uint(width))
    DOUT = X.mkreg(X.Uint(width))
    SEL_DIN = X.mkreg(X.mkarray(X.Uint(width), num_channels))
    SEL_DOUT = X.mkreg(X.mkarray(X.Uint(width), num_channels))

    Switcher(SEL=SEL,
             DIN=DIN,
             SEL_DOUT=SEL_DOUT,
             SEL_DIN=SEL_DIN,
             DOUT=DOUT,
             **{k: locals()[k] for k in Switcher.ARGS.keys()})

  @X.hdl_process()
  def init(self):
    import random

    from pyxhdl import testbench as TB

    for i in range(num_tests):
      chaddr = random.randint(0, num_channels - 1)
      data = random.randint(0, 2**width - 1)
      odata = random.randint(0, 2**width - 1)

      SEL = chaddr
      DIN = data
      SEL_DIN[chaddr] = odata

      XL.wait_for(1e-9)

      TB.compare_value(SEL_DOUT[chaddr], data)
      TB.compare_value(DOUT, odata)

    XL.finish()

