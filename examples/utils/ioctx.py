import pyxhdl as X
from pyxhdl import xlib as XL


class IoctxIfc(X.Interface):

  IFC = 'CLK, RST_N, M_TREADY, =M_TDATA, =M_TVALID, =M_TLAST, =S_TREADY, S_TDATA, ' \
    'S_TVALID, S_TLAST, RDEN, WREN, CHADDR, WDATA, =RDATA, =RREADY, =WREADY, =ERROR'

  def __init__(self, clk, reset, *,
               num_channels=4,
               width=8):
    super().__init__('IOCTX',
                     num_channels=num_channels,
                     width=width)
    self.mkfield('CLK', clk)
    self.mkfield('RST_N', reset)

    # Master signals.
    self.mkfield('M_TREADY', X.Bits(num_channels))
    self.mkfield('M_TDATA', X.mkarray(X.Bits(width), num_channels))
    self.mkfield('M_TVALID', X.Bits(num_channels))
    self.mkfield('M_TLAST', X.Bits(num_channels))

    # Slave signals.
    self.mkfield('S_TREADY', X.Bits(num_channels))
    self.mkfield('S_TDATA', X.mkarray(X.Bits(width), num_channels))
    self.mkfield('S_TVALID', X.Bits(num_channels))
    self.mkfield('S_TLAST', X.Bits(num_channels))

    # Module signals.
    self.mkfield('RDEN', X.BIT)
    self.mkfield('WREN', X.BIT)
    self.mkfield('CHADDR', X.Bits(num_channels.bit_length()))
    self.mkfield('WDATA', X.Bits(width))
    self.mkfield('RDATA', X.Bits(width))
    self.mkfield('RREADY', X.Bits(num_channels))
    self.mkfield('WREADY', X.Bits(num_channels))
    self.mkfield('ERROR', X.UINT4)


class Ioctx(X.Entity):

  PORTS = f'*IFC:{__name__}.IoctxIfc.IFC'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    for i in range(IFC.num_channels):
      IFC.RREADY[i] = IFC.S_TVALID[i]
      IFC.WREADY[i] = not IFC.M_TVALID[i]

  @X.hdl_process(sens='+IFC.CLK')
  def run(self):
    for i in range(IFC.num_channels):
      if IFC.RST_N != 1:
        IFC.M_TVALID[i] = 0
        IFC.M_TLAST[i] = 0
        IFC.S_TREADY[i] = 0
      else:
        IFC.S_TREADY[i] = 0

        if IFC.M_TREADY[i]:
          IFC.M_TVALID[i] = 0

        if IFC.CHADDR == i:
          IFC.ERROR = 0

          if IFC.RDEN:
            if IFC.S_TVALID[i]:
              IFC.S_TREADY[i] = 1
              IFC.RDATA = IFC.S_TDATA[i]
            else:
              IFC.ERROR = 1

          if IFC.WREN:
            if not IFC.M_TVALID[i]:
              IFC.M_TDATA[i] = IFC.WDATA
              IFC.M_TVALID[i] = 1
            else:
              IFC.ERROR = 2

