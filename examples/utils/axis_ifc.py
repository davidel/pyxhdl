import pyxhdl as X


class AxisIfc(X.Interface):

  MASTER = 'CLK, RST_N, TREADY, =TDATA, =TVALID'
  SLAVE = 'CLK, RST_N, =TREADY, TDATA, TVALID'

  def __init__(self, dtype, clk, reset):
    super().__init__('AXIS')
    self.mkfield('CLK', clk)
    self.mkfield('RST_N', reset)
    self.mkfield('TVALID', X.BIT)
    self.mkfield('TREADY', X.BIT)
    self.mkfield('TDATA', dtype)


class AxisMaster(X.Entity):

  PORTS = f'*IFC:{__name__}.AxisIfc.MASTER, WREN, DATA'

  @X.hdl_process(sens='+IFC.CLK')
  def run():
    if IFC.RST_N != 1:
      IFC.TVALID = 0
    else:
      if WREN:
        IFC.TDATA = DATA
        IFC.TVALID = 1
      elif IFC.TREADY:
        IFC.TVALID = 0


class AxisSlave(X.Entity):

  PORTS = f'*IFC:{__name__}.AxisIfc.SLAVE, =RDEN, =DATA'

  @X.hdl_process(sens='+IFC.CLK')
  def run():
    if IFC.RST_N != 1:
      IFC.TREADY = 0
      RDEN = 0
    else:
      if IFC.TVALID:
        DATA = IFC.TDATA
        RDEN = 1
        IFC.TREADY = 1
      else:
        RDEN = 0
        IFC.TREADY = 0


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

    self.ifc = AxisIfc(X.Bits(width), CLK, RST_N)

    WDATA = X.mkreg(X.Bits(width))
    WREN = X.mkreg(X.BIT)
    RDATA = X.mkreg(X.Bits(width))
    RDEN = X.mkreg(X.BIT)

    AxisMaster(IFC=self.ifc,
               WREN=WREN,
               DATA=WDATA)

    AxisSlave(IFC=self.ifc,
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

