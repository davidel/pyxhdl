import pyxhdl as X
from pyxhdl import xlib as XL


class AndGate(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def run():
    XOUT = A & B

