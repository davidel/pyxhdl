import pyxhdl as X
from pyxhdl import xlib as XL

import edger
import uart


class UartEcho(X.Entity):

  PORTS = 'CLK, RST_N, UIN, =UOUT, CTS, =RTS'

  ARGS = dict(clk_freq=50000000, baud_rate=115200)

  IDLE = 0
  TX_START = 1
  TX_ACTIVE = 2

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    self.uifc = uart.UartIfc(CLK, RST_N, UIN, UOUT, CTS, RTS,
                             **self.kwargs)

    uart.UartTX(IFC=self.uifc)
    uart.UartRX(IFC=self.uifc)

    rxrdy_pedge = X.mkreg(self.uifc.RX_READY.dtype)
    rxrdy_nedge = X.mkreg(self.uifc.RX_READY.dtype)

    edger.Edger(CLK=CLK,
                RST_N=RST_N,
                DIN=self.uifc.RX_READY,
                POUT=rxrdy_pedge,
                NOUT=rxrdy_nedge)

  @X.hdl_process(sens='+CLK')
  def run(self):
    state = X.mkreg(X.UINT8)

    if RST_N != 1:
      self.uifc.TX_EN = 0
      RTS = 0
      state = self.IDLE
    else:
      RTS = self.uifc.RX_BUSY or (self.uifc.RX_READY and not self.uifc.TX_BUSY)

      match state:
        case self.IDLE:
          if CTS == 0 and rxrdy_pedge:
            self.uifc.TX_DATA = self.uifc.RX_DATA
            self.uifc.TX_EN = 1
            state = self.TX_START

        case self.TX_START:
          if self.uifc.TX_BUSY == 1:
            self.uifc.TX_EN = 0
            state = self.TX_ACTIVE

        case self.TX_ACTIVE:
          if self.uifc.TX_BUSY == 0:
            state = self.IDLE

        case _:
          pass
