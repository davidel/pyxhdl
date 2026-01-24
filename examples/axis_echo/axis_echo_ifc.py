import pyxhdl as X
from pyxhdl import xlib as XL


class AxisIfc(X.Interface):

  MASTER = 'RST_N, TREADY, =TDATA, =TVALID'
  SLAVE = 'RST_N, =TREADY, TDATA, TVALID'

  def __init__(self, dtype, reset):
    super().__init__('AXIS')
    self.mkfield('RST_N', reset)
    self.mkfield('TVALID', X.BIT)
    self.mkfield('TREADY', X.BIT)
    self.mkfield('TDATA', dtype)


class AxisMaster(X.Entity):

  PORTS = f'CLK, *IFC:{__name__}.AxisIfc.MASTER, WREN, DATA'

  @X.hdl_process(sens='+CLK')
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

  PORTS = f'CLK, *IFC:{__name__}.AxisIfc.SLAVE, =RDEN, =DATA'

  @X.hdl_process(sens='+CLK')
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


class AxisEcho(X.Entity):

  PORTS = 'CLK, RST_N, WDATA, WREN, =RDATA, =RDEN'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    self.axis_ifc = AxisIfc(WDATA.dtype, RST_N)

    AxisMaster(CLK=CLK,
               IFC=self.axis_ifc,
               WREN=WREN,
               DATA=WDATA)

    AxisSlave(CLK=CLK,
              IFC=self.axis_ifc,
              DATA=RDATA,
              RDEN=RDEN)

