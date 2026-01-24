import pyxhdl as X
from pyxhdl import xlib as XL

import uart


class UartEcho(X.Entity):

  PORTS = 'CLK, RST_N, UIN, =UOUT, CTS, =RTS'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    self.uart_ifc = uart.UartIfc(CLK, RST_N, UIN, UOUT, CTS, RTS,
                                 clk_freq=50000000,
                                 baud_rate=115200)

    uart.UartTX(IFC=self.uart_ifc)

    uart.UartRX(IFC=self.uart_ifc)

