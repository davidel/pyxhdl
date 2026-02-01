import pyxhdl as X
from pyxhdl import xlib as XL


class Clock(X.Entity):

  PORTS = '=CLK=bit'

  def __init__(self, frequency, **kwargs):
    super().__init__(**kwargs)
    self.period = 1.0 / frequency

  @X.hdl_process(proc_mode='loop')
  def run(self):
    CLK = 0
    XL.wait_for(self.period / 2)
    CLK = 1
    XL.wait_for(self.period / 2)

