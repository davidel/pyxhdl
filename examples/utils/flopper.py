import pyxhdl as X
from pyxhdl import xlib as XL


class Flopper(X.Entity):

  PORTS = 'CLK, RST_N, DIN:b0, =DOUT:b0'
  ARGS = dict(stages=1, sides='+-')

  @X.hdl_process(sens='+CLK')
  def run(self):
    prev_din = X.mkreg(X.Bits(stages) if stages > 1 else X.BIT)

    if RST_N != 1:
      prev_din = 0
    else:
      DOUT = prev_din[-1] if stages > 1 else prev_din

      match DIN:
        case 1:
          if '+' in sides:
            prev_din = prev_din[: -1] @ DIN if stages > 1 else 1
          else:
            prev_din = X.bitfill(1, stages)
            DOUT = 1

        case 0:
          if '-' in sides:
            prev_din = prev_din[: -1] @ DIN if stages > 1 else 0
          else:
            prev_din = X.bitfill(0, stages)
            DOUT = 0

        case _:
          pass


class Test(X.Entity):

  ARGS = dict(clock_frequency=100e6) | Flopper.ARGS

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    from . import clock

    CLK = X.mkreg(X.BIT)

    clock.Clock(CLK=CLK,
                frequency=clock_frequency)

    RST_N = X.mkreg(X.BIT)
    DIN = X.mkreg(X.BIT)
    DOUT = X.mkreg(X.BIT)

    Flopper(CLK=CLK,
            RST_N=RST_N,
            DIN=DIN,
            DOUT=DOUT,
            **{k: locals()[k] for k in Flopper.ARGS.keys()})

  @X.hdl_process(kind=X.INIT_PROCESS)
  def test_run(self):
    from pyxhdl import testbench as TB

    RST_N = 0
    DIN = 0

    TB.wait_rising(CLK)

    RST_N = 1

    DIN = 1
    if '+' in sides:
      for _ in range(stages):
        TB.wait_rising(CLK)

      TB.compare_value(DOUT, 0)

      TB.wait_rising(CLK)
      TB.compare_value(DOUT, 1)
    else:
      TB.wait_rising(CLK)
      TB.compare_value(DOUT, 1)

    DIN = 0
    if '-' in sides:
      for _ in range(stages):
        TB.wait_rising(CLK)

      TB.compare_value(DOUT, 1)

      TB.wait_rising(CLK)
      TB.compare_value(DOUT, 0)
    else:
      TB.wait_rising(CLK)
      TB.compare_value(DOUT, 0)

    XL.finish()

