import pyxhdl as X
from pyxhdl import xlib as XL

import uart


class UartEcho(X.Entity):

  PORTS = 'CLK, RST_N, UIN, =UOUT, CTS, =RTS'

  IDLE = 0
  TX_START = 1
  TX_ACTIVE = 2

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    self.uifc = uart.UartIfc(CLK, RST_N, UIN, UOUT, CTS, RTS,
                             clk_freq=50000000,
                             baud_rate=115200)

    uart.UartTX(IFC=self.uifc)
    uart.UartRX(IFC=self.uifc)

  @X.hdl_process(sens='+CLK')
  def run(self):
    state = X.mkreg(X.UINT8)

    if RST_N != 1:
      state = self.IDLE
      RTS = 0
    else:
      RTS = self.uifc.RX_BUSY

      match state:
        case self.IDLE:
          if CTS == 0 and self.uifc.RX_READY == 1:
            self.uifc.TX_DATA = self.uifc.RX_DATA
            self.uifc.TX_EN = 1
            state = self.TX_START

        case self.TX_START:
          if self.uifc.TX_BUSY == 1:
            state = self.TX_ACTIVE

        case self.TX_ACTIVE:
          if self.uifc.TX_BUSY == 0:
            state = self.IDLE

        case _:
          pass
