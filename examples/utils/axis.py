import pyxhdl as X


class AxisMaster(X.Entity):

  PORTS = 'CLK, RST_N, WREN, DATA, TREADY, =TDATA, =TVALID'

  @X.hdl_process(sens='+CLK')
  def run():
    if RST_N != 1:
      TVALID = 0
    else:
      if WREN:
        TDATA = DATA
        TVALID = 1
      elif TREADY:
        TVALID = 0


class AxisSlave(X.Entity):

  PORTS = 'CLK, RST_N, TDATA, TVALID, =TREADY, =DATA, =RDEN'

  @X.hdl_process(sens='+CLK')
  def run():
    if RST_N != 1:
      TREADY = 0
      RDEN = 0
    else:
      if TVALID:
        DATA = TDATA
        RDEN = 1
        TREADY = 1
      else:
        RDEN = 0
        TREADY = 0


class Test(X.Entity):

  ARGS = dict(clock_frequency=100e6,
              num_tests=20,
              width=8)

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    from . import clock

    CLK = X.mkreg(X.BIT)

    clock.Clock(CLK=CLK,
                frequency=clock_frequency)

    RST_N = X.mkreg(X.BIT)

    TVALID = X.mkreg(X.BIT)
    TREADY = X.mkreg(X.BIT)

    WDATA = X.mkreg(X.Bits(width))
    WREN = X.mkreg(X.BIT)
    RDATA = X.mkreg(X.Bits(width))
    RDEN = X.mkreg(X.BIT)

    DATA = X.mkreg(X.Bits(width))

    AxisMaster(CLK=CLK,
               RST_N=RST_N,
               WREN=WREN,
               DATA=WDATA,
               TREADY=TREADY,
               TDATA=DATA,
               TVALID=TVALID)

    AxisSlave(CLK=CLK,
              RST_N=RST_N,
              TDATA=DATA,
              TVALID=TVALID,
              TREADY=TREADY,
              DATA=RDATA,
              RDEN=RDEN)

  @X.hdl_process(kind=X.INIT_PROCESS)
  def test_run(self):
    import random

    from pyxhdl import xlib as XL
    from pyxhdl import testbench as TB

    RST_N = 0

    TB.wait_rising(CLK)
    TB.wait_rising(CLK)

    RST_N = 1

    TB.wait_rising(CLK)

    value_mask = 2**width - 1

    for i in range(num_tests):
      value = random.randint(0, value_mask)

      WDATA = value
      WREN = 1

      TB.wait_rising(CLK)
      TB.wait_until(CLK, RDEN == 1)

      TB.compare_value(RDATA, value)

      TB.wait_rising(CLK)

    XL.finish()

