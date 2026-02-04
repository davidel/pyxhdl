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
    self.mkfield('M_TREADY', X.mkarray(X.BIT, num_channels))
    self.mkfield('M_TDATA', X.mkarray(X.Bits(width), num_channels))
    self.mkfield('M_TVALID', X.mkarray(X.BIT, num_channels))
    self.mkfield('M_TLAST', X.mkarray(X.BIT, num_channels))

    # Slave signals.
    self.mkfield('S_TREADY', X.mkarray(X.BIT, num_channels))
    self.mkfield('S_TDATA', X.mkarray(X.Bits(width), num_channels))
    self.mkfield('S_TVALID', X.mkarray(X.BIT, num_channels))
    self.mkfield('S_TLAST', X.mkarray(X.BIT, num_channels))

    # Module signals.
    self.mkfield('RDEN', X.BIT)
    self.mkfield('WREN', X.BIT)
    self.mkfield('CHADDR', X.Uint(num_channels.bit_length()))
    self.mkfield('WDATA', X.Bits(width))
    self.mkfield('RDATA', X.Bits(width))
    self.mkfield('RREADY', X.mkarray(X.BIT, num_channels))
    self.mkfield('WREADY', X.mkarray(X.BIT, num_channels))
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


class Test(X.Entity):

  ARGS = dict(clock_frequency=100e6,
              num_tests=20,
              num_channels=8,
              width=8) | Ioctx.ARGS

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    import py_misc_utils.module_utils as pymu

    from . import clock

    axis = pymu.rel_import_module('../utils/axis', __file__)

    CLK = X.mkreg(X.BIT)

    clock.Clock(CLK=CLK,
                frequency=clock_frequency)

    RST_N = X.mkreg(X.BIT)

    self.ifc = IoctxIfc(CLK, RST_N,
                        num_channels=num_channels,
                        width=width)

    Ioctx(IFC=self.ifc,
          **{k: locals()[k] for k in Ioctx.ARGS.keys()})

    RDEN = X.mkvreg(X.mkarray(X.BIT, num_channels), 0)
    DATA = X.mkreg(self.ifc.M_TDATA.dtype)

    for i in range(num_channels):
      axis.AxisMaster(CLK=CLK,
                      RST_N=RST_N,
                      WREN=RDEN[i],
                      DATA=DATA[i],
                      TREADY=self.ifc.S_TREADY[i],
                      TDATA=self.ifc.S_TDATA[i],
                      TVALID=self.ifc.S_TVALID[i])

      axis.AxisSlave(CLK=CLK,
                     RST_N=RST_N,
                     TDATA=self.ifc.M_TDATA[i],
                     TVALID=self.ifc.M_TVALID[i],
                     TREADY=self.ifc.M_TREADY[i],
                     DATA=DATA[i],
                     RDEN=RDEN[i])

  @X.hdl_process()
  def init(self):
    import random

    from pyxhdl import testbench as TB

    RST_N = 0
    self.ifc.RDEN = 0
    self.ifc.WREN = 0

    TB.wait_rising(CLK)

    RST_N = 1

    for i in range(num_tests):
      data = random.randint(0, 2**width - 1)
      chaddr = random.randint(0, num_channels - 1)

      self.ifc.CHADDR = chaddr

      XL.wait_until(self.ifc.WREADY[chaddr] == 1)

      self.ifc.WDATA = data
      self.ifc.WREN = 1
      TB.wait_rising(CLK)
      self.ifc.WREN = 0

      TB.wait_rising(CLK)

      XL.wait_until(self.ifc.RREADY[chaddr] == 1)

      self.ifc.RDEN = 1
      TB.wait_rising(CLK)
      self.ifc.RDEN = 0

      TB.compare_value(self.ifc.RDATA, data)

    XL.finish()

