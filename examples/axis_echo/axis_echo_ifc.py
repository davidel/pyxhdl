import py_misc_utils.module_utils as pymu

import pyxhdl as X
from pyxhdl import xlib as XL

axis = pymu.rel_import_module('../utils/axis_ifc', __file__)


class AxisEcho(X.Entity):

  PORTS = 'CLK=bit, RST_N=bit, WDATA, WREN=bit, =RDATA, =RDEN=bit'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    self.axis_ifc = axis.AxisIfc(WDATA.dtype, CLK, RST_N)

    axis.AxisMaster(IFC=self.axis_ifc,
                    WREN=WREN,
                    DATA=WDATA)

    axis.AxisSlave(IFC=self.axis_ifc,
                   DATA=RDATA,
                   RDEN=RDEN)

