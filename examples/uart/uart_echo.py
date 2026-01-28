import py_misc_utils.module_utils as pymu

import pyxhdl as X
from pyxhdl import xlib as XL

uart = pymu.rel_import_module('../utils/uart')


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

  @X.hdl_process(sens='+CLK')
  def run(self):
    state = X.mkreg(X.UINT8)
    rx_reset = X.mkreg(X.BIT)

    if RST_N != 1:
      self.uifc.TX_EN = 0
      RTS = 0
      rx_reset = 1
      state = self.IDLE
    else:
      RTS = self.uifc.RX_BUSY or (self.uifc.RX_READY and not self.uifc.TX_BUSY)

      if not self.uifc.RX_READY:
        rx_reset = 1

      match state:
        case self.IDLE:
          if CTS == 0 and self.uifc.RX_READY and rx_reset:
            self.uifc.TX_DATA = self.uifc.RX_DATA
            self.uifc.TX_EN = 1
            rx_reset = 0
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
