import pyxhdl as X
from pyxhdl import xlib as XL


class AutoReset(X.Entity):

  PORTS = 'CLK=bit, =RST=bit'

  ARGS = dict(start_clocks=0, clocks_count=1, polarity=-1)

  @X.hdl_process(sens='+CLK')
  def run(self):
    max_count = start_clocks + clocks_count
    count = X.mkvreg(X.Uint(max_count.bit_length()), 0)

    if count == max_count:
      RST = 0 if polarity >= 0 else 1
    else:
      if start_clocks == 0 or count > start_clocks:
        RST = 1 if polarity >= 0 else 0
      else:
        RST = 0 if polarity >= 0 else 1

      count += 1

