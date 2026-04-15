import pyxhdl as X


class Blinky(X.Entity):

  PORTS = 'CLK=bit, RST_N=bit, =LED=bit'
  ARGS = dict(clk_freq_hz=10e6, led_period_sec=1.0)

  @X.hdl_process(sens='+CLK')
  def blinker():
    trigger_count = int(clk_freq_hz * led_period_sec)

    counter = X.mkreg(X.Uint(trigger_count.bit_length()))

    if RST_N != 1:
      counter = 0
      LED = 0
    elif counter == trigger_count:
      LED = ~LED
      counter = 0
    else:
      counter += 1

