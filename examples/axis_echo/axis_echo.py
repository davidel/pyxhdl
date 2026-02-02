import py_misc_utils.module_utils as pymu

import pyxhdl as X
from pyxhdl import xlib as XL

axis = pymu.rel_import_module('../utils/axis')


class AxisEcho(X.Entity):

  PORTS = 'CLK=bit, RST_N=bit, WDATA, WREN=bit, =RDATA, =RDEN=bit'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root():
    TVALID = X.mkreg(X.BIT)
    TREADY = X.mkreg(X.BIT)
    TDATA = X.mkreg(WDATA.dtype)

    axis.AxisMaster(CLK=CLK,
                    RST_N=RST_N,
                    WREN=WREN,
                    DATA=WDATA,
                    TREADY=TREADY,
                    TDATA=TDATA,
                    TVALID=TVALID)

    axis.AxisSlave(CLK=CLK,
                   RST_N=RST_N,
                   TDATA=TDATA,
                   TVALID=TVALID,
                   TREADY=TREADY,
                   DATA=RDATA,
                   RDEN=RDEN)

