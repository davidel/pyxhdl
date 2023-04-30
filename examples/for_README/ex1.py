import pyxhdl as X
from pyxhdl import xlib as XL


class Ex1(X.Entity):

  PORTS = 'CLK, A, B, =XOUT'

  @X.hdl_process(sens='+CLK')
  def run():
    XOUT = A + B

