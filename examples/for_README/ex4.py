import pyxhdl as X
from pyxhdl import xlib as XL

class Asserty(X.Entity):

  PORTS = 'CLK, A, B, =XOUT'

  @X.hdl_process(sens='+CLK')
  def run():
    assert ((A > 5) and (B < 11)) or (A + B) > 17, f'Assert failed: {{A}} {{B}}'
    XOUT = A * 3 - (B >> 1)


class Ex4(X.Entity):

  PORTS = 'CLK, A, B, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root():
    Asserty(CLK=CLK, A=B, B=B, XOUT=XOUT)

