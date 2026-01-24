import pyxhdl as X
from pyxhdl import xlib as XL


class UartIfc(X.Interface):

  TX = 'CLK, RST_N, TX_DATA, TX_EN, =UOUT, =TX_BUSY'
  RX = 'CLK, RST_N, UIN, =RX_BUSY, =RX_READY, =RX_DATA'

  def __init__(self, clk, reset, uin, uout, cts, rts):
    super().__init__('UART')
    self.mkfield('CLK', clk)
    self.mkfield('RST_N', reset)
    self.mkfield('UIN', uin)
    self.mkfield('UOUT', uout)
    self.mkfield('CTS', cts)
    self.mkfield('RTS', rts)
    self.mkfield('TX_EN', X.BIT)
    self.mkfield('TX_BUSY', X.BIT)
    self.mkfield('TX_DATA', X.Bits(8))
    self.mkfield('RX_BUSY', X.BIT)
    self.mkfield('RX_READY', X.BIT)
    self.mkfield('RX_DATA', X.Bits(8))


class UartTX(X.Entity):

  PORTS = f'*IFC:{__name__}.UartIfc.TX'

  @X.hdl_process(sens='+IFC.CLK')
  def run():
    if not IFC.RST_N:
      IFC.TVALID = 0
    else:
      if WREN:
        IFC.TDATA = DATA
        IFC.TVALID = 1
      elif IFC.TREADY:
        IFC.TVALID = 0


class UartRX(X.Entity):

  PORTS = f'*IFC:{__name__}.UartIfc.RX'

  @X.hdl_process(sens='+IFC.CLK')
  def run():
    if not IFC.RST_N:
      IFC.TREADY = 0
      RDEN = 0
    else:
      if IFC.TVALID:
        DATA = IFC.TDATA
        RDEN = 1
        IFC.TREADY = 1
      else:
        RDEN = 0


class UartEcho(X.Entity):

  PORTS = 'CLK, RST_N, UIN, =UOUT, CTS, =RTS'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    self.uart_ifc = UartIfc(CLK, RST_N, UIN, UOUT, CTS, RTS)

    UartTX(IFC=self.axis_ifc,
           WREN=WREN,
           DATA=WDATA)

    UartRX(IFC=self.axis_ifc,
           DATA=RDATA,
           RDEN=RDEN)

