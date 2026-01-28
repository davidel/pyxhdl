import pyxhdl as X
from pyxhdl import xlib as XL


class ClkTrigger(X.Entity):

  PORTS = 'CLK, RST_N, COUNT, EN, =ACTIVE'

  @X.hdl_process(sens='+CLK')
  def run(self):
    enabled = X.mkreg(X.BIT)
    count = X.mkreg(COUNT.dtype)
    counter = X.mkreg(COUNT.dtype)

    if RST_N != 1:
      ACTIVE = 0
      enabled = 0
      count = 0
      counter = 0
    else:
      if not EN:
        enabled = 0
        ACTIVE = 0
      elif enabled:
        if not ACTIVE:
          if counter + 1 == count:
            ACTIVE = 1
          else:
            counter += 1
      else:
        count = COUNT
        counter = 0
        enabled = 1
        if COUNT == 0:
          ACTIVE = 1

