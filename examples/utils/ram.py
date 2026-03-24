import math

import py_misc_utils.assert_checks as tas
import py_misc_utils.num_utils as pynu

import pyxhdl as X


class RamIfc(X.Interface):

  PORT = 'CLK, RST_N, WREN, RDEN, =READY, ADDR, WDATA, =RDATA'

  def __init__(self, clk, reset, width, size,
               unit_size=8):
    tas.check_eq(width % unit_size, 0,
                 msg=f'Word size ({width}) must be multiple of unit size ({unit_size})')

    word_units = width // unit_size
    addr_size = pynu.address_bits(size)

    super().__init__('RAM',
                     width=width,
                     size=size,
                     addr_size=addr_size,
                     unit_size=unit_size,
                     word_units=word_units)
    self.mkfield('CLK', clk)
    self.mkfield('RST_N', reset)
    self.mkfield('WREN', X.BIT)
    self.mkfield('RDEN', X.BIT)
    self.mkfield('READY', X.BIT)
    self.mkfield('ADDR', X.Uint(addr_size))
    self.mkfield('WDATA', X.Bits(width))
    self.mkfield('RDATA', X.Bits(width))


class Ram(X.Entity):

  PORTS = f'*IFC:{__name__}.RamIfc.PORT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    mem = X.mkreg(X.mkarray(IFC.RDATA.dtype, IFC.size))

    rddata = X.mkreg(X.Bits(2 * IFC.width))
    unawr = X.mkreg(X.BIT)

    baddr = X.mkwire(IFC.ADDR.dtype)
    baddr = (IFC.ADDR % IFC.word_units) * IFC.unit_size
    IFC.RDATA = rddata[baddr:: IFC.width]

  @X.hdl_process(sens='+IFC.CLK')
  def run(self):
    waddr = X.mkwire(IFC.ADDR.dtype)
    wbaddr = X.mkwire(IFC.ADDR.dtype)
    wrdata = X.mkwire(X.Bits(2 * IFC.width))

    if IFC.RST_N != 1:
      IFC.READY = 0
      rddata = X.bitfill('X', rddata.dtype.nbits)
      unawr = 0
    elif IFC.RDEN == 1:
      waddr = IFC.ADDR / IFC.word_units
      rddata[0: IFC.width] = mem[waddr]
      rddata[IFC.width: ] = mem[waddr + 1]

      IFC.READY = 1
    elif IFC.WREN == 1:
      waddr = IFC.ADDR / IFC.word_units
      if IFC.ADDR % IFC.word_units == 0:
        mem[waddr] = IFC.WDATA
        IFC.READY = 1
      else:
        rddata[0: IFC.width] = mem[waddr]
        rddata[IFC.width: ] = mem[waddr + 1]

        if unawr == 0:
          unawr = 1
        else:
          wrdata = rddata
          wbaddr = (IFC.ADDR % IFC.word_units) * IFC.unit_size
          wrdata[baddr:: IFC.width] = IFC.WDATA
          mem[waddr] = wrdata[0: IFC.width]
          mem[waddr + 1] = wrdata[IFC.width: ]
          IFC.READY = 1
    else:
      IFC.READY = 0
      unawr = 0


class Test(X.Entity):

  ARGS = dict(clock_frequency=100e6,
              num_tests=50,
              width=32,
              size=4096,
              unit_size=8)

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    from . import clock

    CLK = X.mkreg(X.BIT)

    clock.Clock(CLK=CLK,
                frequency=clock_frequency)

    RST_N = X.mkreg(X.BIT)

    self.ifc = RamIfc(CLK, RST_N, width, size,
                      unit_size=unit_size)

    Ram(IFC=self.ifc)

  @X.hdl_process()
  def run(self):
    import random

    from pyxhdl import xlib as XL
    from pyxhdl import testbench as TB

    RST_N = 0
    self.ifc.WREN = 0
    self.ifc.RDEN = 0
    self.ifc.ADDR = 0

    TB.wait_rising(CLK)
    TB.wait_rising(CLK)

    RST_N = 1

    TB.wait_rising(CLK)

    for i in range(num_tests):
      addr = random.randint(0, size - width // unit_size)
      value = random.randint(0, 2 ** width - 1)

      self.ifc.WREN = 1
      self.ifc.ADDR = addr
      self.ifc.WDATA = value

      TB.wait_until(CLK, self.ifc.READY == 1)

      self.ifc.WREN = 0
      TB.wait_rising(CLK)

      self.ifc.RDEN = 1

      TB.wait_until(CLK, self.ifc.READY == 1)

      TB.compare_value(self.ifc.RDATA, value,
                       msg=f' : addr={addr}')

      self.ifc.RDEN = 0
      TB.wait_rising(CLK)

    XL.finish()

