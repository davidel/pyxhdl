import pyxhdl as X
from pyxhdl import xlib as XL


class Edger(X.Entity):

  PORTS = 'CLK, RST_N, DIN, =POUT, =NOUT'

  @X.hdl_process(sens='+CLK')
  def run(self):
    prev_din = X.mkreg(DIN.dtype)

    if RST_N != 1:
      prev_din = DIN
      POUT = 0
      NOUT = 0
    else:
      POUT = DIN & (~prev_din)
      NOUT = prev_din & (~DIN)
      prev_din = DIN

