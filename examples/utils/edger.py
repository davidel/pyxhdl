import pyxhdl as X
from pyxhdl import xlib as XL


class Edger(X.Entity):

  PORTS = 'CLK, RST_N, DIN, =POUT, =NOUT'

  @X.hdl_process(sens='+CLK')
  def run(self):
    prev_din = X.mkreg(DIN.dtype)

    if RST_N != 1:
      prev_din = DIN
      POUT = 0
      NOUT = 0
    else:
      POUT = DIN & (~prev_din)
      NOUT = prev_din & (~DIN)
      prev_din = DIN


class Test(X.Entity):

  ARGS = dict(clock_frequency=100e6) | Edger.ARGS

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    from . import clock

    CLK = X.mkreg(X.BIT)

    clock.Clock(CLK=CLK,
                frequency=clock_frequency)

    RST_N = X.mkreg(X.BIT)
    DIN = X.mkreg(X.BIT)
    POUT = X.mkreg(X.BIT)
    NOUT = X.mkreg(X.BIT)

    Edger(CLK=CLK,
          RST_N=RST_N,
          DIN=DIN,
          POUT=POUT,
          NOUT=NOUT,
          **{k: locals()[k] for k in Edger.ARGS.keys()})

  @X.hdl_process()
  def init(self):
    from pyxhdl import testbench as TB

    RST_N = 0
    DIN = 0

    XL.wait_rising(CLK)
    XL.wait_rising(CLK)

    RST_N = 1
    DIN = 1

    XL.wait_rising(CLK)

    TB.compare_value(POUT, 1)
    TB.compare_value(NOUT, 0)

    DIN = 0

    XL.wait_rising(CLK)

    TB.compare_value(POUT, 0)
    TB.compare_value(NOUT, 1)

    XL.finish()

