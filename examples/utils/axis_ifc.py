import pyxhdl as X
from pyxhdl import xlib as XL


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
    if not IFC.RST_N:
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
    if not IFC.RST_N:
      IFC.TREADY = 0
      RDEN = 0
    else:
      if IFC.TVALID:
        DATA = IFC.TDATA
        RDEN = 1
        IFC.TREADY = 1
      else:
        RDEN = 0

