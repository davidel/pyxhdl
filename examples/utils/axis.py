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

