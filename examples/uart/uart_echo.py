import pyxhdl as X
from pyxhdl import xlib as XL

import uart


class UartEcho(X.Entity):

  PORTS = 'CLK, RST_N, UIN, =UOUT, CTS, =RTS'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    self.uifc = uart.UartIfc(CLK, RST_N, UIN, UOUT, CTS, RTS,
                             clk_freq=50000000,
                             baud_rate=115200)

    uart.UartTX(IFC=self.uifc)
    uart.UartRX(IFC=self.uifc)

  @X.hdl_process(sens='+CLK')
  def run(self):
    if RST_N == 1:
      if self.uifc.RX_READY:
        self.uifc.TX_DATA = self.uifc.RX_DATA
        self.uifc.TX_EN = 1

