import pyxhdl as X
from pyxhdl import xlib as XL


class AxisMaster(X.Entity):

  PORTS = 'CLK, RST_N, WREN, DATA, TREADY, =TDATA, =TVALID'

  @X.hdl_process(sens='+CLK')
  def run():
    if not RST_N:
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
    if not RST_N:
      TREADY = 0
      RDEN = 0
    else:
      if TVALID:
        DATA = TDATA
        RDEN = 1
        TREADY = 1
      else:
        RDEN = 0


class AxisEcho(X.Entity):

  PORTS = 'CLK, RST_N, WDATA, WREN, =RDATA, =RDEN'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root():
    TVALID = X.mkreg(X.BIT)
    TREADY = X.mkreg(X.BIT)
    TDATA = X.mkreg(WDATA.dtype)

    AxisMaster(CLK=CLK,
               RST_N=RST_N,
               WREN=WREN,
               DATA=WDATA,
               TREADY=TREADY,
               TDATA=TDATA,
               TVALID=TVALID)

    AxisSlave(CLK=CLK,
              RST_N=RST_N,
              TDATA=TDATA,
              TVALID=TVALID,
              TREADY=TREADY,
              DATA=RDATA,
              RDEN=RDEN)

