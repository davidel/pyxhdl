import pyxhdl as X
from pyxhdl import xlib as XL


class UartIfc(X.Interface):

  TX = 'CLK, RST_N, TX_DATA, TX_EN, =UOUT, =TX_BUSY'
  RX = 'CLK, RST_N, UIN, =RX_BUSY, =RX_READY, =RX_DATA'

  def __init__(self, clk, reset, uin, uout, cts, rts, *,
               clk_freq=50000000,
               baud_rate=115200,
               word_size=8):
    super().__init__('UART',
                     clk_freq=clk_freq,
                     baud_rate=baud_rate,
                     clks_per_bit=clk_freq // baud_rate)
    self.mkfield('CLK', clk)
    self.mkfield('RST_N', reset)
    self.mkfield('UIN', uin)
    self.mkfield('UOUT', uout)
    self.mkfield('CTS', cts)
    self.mkfield('RTS', rts)
    self.mkfield('TX_EN', X.BIT)
    self.mkfield('TX_BUSY', X.BIT)
    self.mkfield('TX_DATA', X.Bits(word_size))
    self.mkfield('RX_BUSY', X.BIT)
    self.mkfield('RX_READY', X.BIT)
    self.mkfield('RX_DATA', X.Bits(word_size))


class UartTX(X.Entity):

  PORTS = f'*IFC:{__name__}.UartIfc.TX'

  IDLE = 0
  DATA = 1
  STOP = 2

  @X.hdl_process(sens='+IFC.CLK')
  def run(self):
    state = X.mkreg(X.UINT8)
    clk_counter = X.mkreg(X.Uint(IFC.clks_per_bit.bit_length()))
    bit_counter = X.mkreg(X.UINT8)
    tx_data = X.mkreg(IFC.TX_DATA.dtype)

    if not IFC.RST_N:
      state = self.IDLE
      clk_counter = 0
      bit_counter = 0
      IFC.UOUT = 1
      IFC.TX_BUSY = 0
    elif clk_counter == IFC.clks_per_bit - 1:
      clk_counter = 0

      match state:
        case self.IDLE:
          if IFC.TX_EN:
            if not IFC.TX_BUSY:
              tx_data = IFC.TX_DATA
              IFC.UOUT = 0
              bit_counter = 0
              IFC.TX_BUSY = 1
              state = self.DATA
          else:
            IFC.TX_BUSY = 0
            IFC.UOUT = 1

        case self.DATA:
          IFC.UOUT = tx_data[0]
          tx_data = tx_data >> 1
          if bit_counter == tx_data.dtype.nbits - 1:
            state = self.STOP
          else:
            bit_counter += 1

        case self.STOP:
          IFC.UOUT = 1
          state = self.IDLE

        case _:
          pass
    else:
      clk_counter += 1


class UartRX(X.Entity):

  PORTS = f'*IFC:{__name__}.UartIfc.RX'

  @X.hdl_process(sens='+IFC.CLK')
  def run(self):
    if not IFC.RST_N:
      pass
    else:
      pass


class UartEcho(X.Entity):

  PORTS = 'CLK, RST_N, UIN, =UOUT, CTS, =RTS'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    self.uart_ifc = UartIfc(CLK, RST_N, UIN, UOUT, CTS, RTS,
                            clk_freq=50000000,
                            baud_rate=115200)

    UartTX(IFC=self.axis_ifc)

    UartRX(IFC=self.axis_ifc)

