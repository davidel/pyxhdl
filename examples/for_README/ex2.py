import pyxhdl as X
from pyxhdl import xlib as XL


class Ex2(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def run():
    temp = X.mkwire(A.dtype)
    temp = A + B
    XOUT = temp * 3

