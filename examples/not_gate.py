import pyxhdl as X
from pyxhdl import xlib as XL


class NotGate(X.Entity):

  PORTS = 'A, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def run():
    XOUT = ~A

