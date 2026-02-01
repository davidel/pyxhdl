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


class Test(X.Entity):

  ARGS = dict(clock_frequency=100e6) | AutoReset.ARGS

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    from . import clock

    CLK = X.mkreg(X.BIT)

    clock.Clock(CLK=CLK,
                frequency=clock_frequency)

    RST = X.mkvreg(X.BIT, 0)

    AutoReset(CLK=CLK,
              RST=RST,
              **{k: locals()[k] for k in AutoReset.ARGS.keys()})

  @X.hdl_process()
  def init(self):
    period = 1 / clock_frequency

    XL.wait_for((start_clocks + 1) * period)
    if polarity > 0 and RST != 1:
      XL.report(f'{{NOW}} Wrong reset value: RST={{RST}}')
    if polarity < 0 and RST != 0:
      XL.report(f'{{NOW}} Wrong reset value: RST={{RST}}')

    XL.wait_for(clocks_count * period)
    if polarity > 0 and RST != 0:
      XL.report(f'{{NOW}} Wrong reset value: RST={{RST}}')
    if polarity < 0 and RST != 1:
      XL.report(f'{{NOW}} Wrong reset value: RST={{RST}}')

    XL.finish()

