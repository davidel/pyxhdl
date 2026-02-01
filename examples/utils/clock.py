import pyxhdl as X
from pyxhdl import xlib as XL


class Clock(X.Entity):

  PORTS = '=CLK=bit'

  def __init__(self, frequency, **kwargs):
    super().__init__(**kwargs)
    self.period = 1.0 / frequency

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    XCLK = X.mkvreg(CLK.dtype, 0)

    CLK = XCLK

  @X.hdl_process()
  def run(self):
    XCLK = not XCLK
    XL.wait_for(self.period / 2)

