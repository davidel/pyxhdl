import math

import py_misc_utils.assert_checks as tas
import py_misc_utils.core_utils as pycu
import py_misc_utils.num_utils as pynu

import pyxhdl as X


class RamIfc(X.Interface):

  PORT = 'CLK, RST_N, WREN, RDEN, =READY, ADDR, WDATA, =RDATA'

  def __init__(self, clk, reset, width, size,
               unit_size=8,
               tdp_ram=False):
    tas.check_eq(width % unit_size, 0,
                 msg=f'Word size ({width}) must be multiple of unit size ({unit_size})')

    word_units = width // unit_size

    super().__init__('RAM',
                     width=width,
                     size=size,
                     unit_size=unit_size,
                     word_units=word_units,
                     tdp_ram=tdp_ram)
    self.mkfield('CLK', clk)
    self.mkfield('RST_N', reset)
    self.mkfield('WREN', X.Uint(word_units.bit_length()))
    self.mkfield('RDEN', X.BIT)
    self.mkfield('READY', X.BIT)
    self.mkfield('ADDR', X.Uint(pynu.address_bits(size)))
    self.mkfield('WDATA', X.Bits(width))
    self.mkfield('RDATA', X.Bits(width))


@X.hdl
def bitmux(orig, base, value, nr, usize) -> X.Value:
  bmres = X.mkwire(orig.dtype)

  bmres = orig

  nsteps = value.dtype.nbits // usize
  for i in range(1, nsteps + 1):
    if nr == i:
      bmres[base:: i * usize] = value[0: i * usize]

  return bmres


class Ram(X.Entity):

  PORTS = f'*IFC:{__name__}.RamIfc.PORT'

  WR_STATE = pycu.make_enum('WR_STATE', 'IDLE, WR_LOW, WR_HIGH')

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    mem = X.mkreg(X.mkarray(IFC.RDATA.dtype, IFC.size))
    rddata = X.mkreg(X.Bits(2 * IFC.width))
    wrdata = X.mkreg(X.Bits(2 * IFC.width))
    wr_state = X.mkreg(X.Uint(self.WR_STATE._last.bit_length()))
    waddr = X.mkwire(IFC.ADDR.dtype)
    baddr = X.mkwire(IFC.ADDR.dtype)
    ovfl = X.mkwire(X.BIT)

    ovfl = '0b1' if (IFC.ADDR % IFC.word_units) + IFC.WREN >= IFC.word_units else '0b0'
    waddr = IFC.ADDR / IFC.word_units
    baddr = (IFC.ADDR % IFC.word_units) * IFC.unit_size
    IFC.RDATA = rddata[baddr:: IFC.width]

  @X.hdl_process(sens='+IFC.CLK')
  def run(self):
    if IFC.RST_N != 1:
      IFC.READY = 0
      rddata = X.bitfill('X', rddata.dtype.nbits)
      wr_state = self.WR_STATE.IDLE
    elif IFC.RDEN == 1:
      rddata[0: IFC.width] = mem[waddr]
      rddata[IFC.width: ] = mem[waddr + 1]

      IFC.READY = 1
    elif IFC.WREN != 0:
      out_data = bitmux(wrdata, baddr, IFC.WDATA, IFC.WREN, IFC.unit_size)

      match wr_state:
        case self.WR_STATE.IDLE:
          wrdata[0: IFC.width] = mem[waddr]
          wrdata[IFC.width: ] = mem[waddr + 1]
          IFC.READY = 0
          wr_state = self.WR_STATE.WR_LOW

        case self.WR_STATE.WR_LOW:
          mem[waddr] = out_data[0: IFC.width]
          if IFC.tdp_ram:
            mem[waddr + 1] = out_data[IFC.width: ]
            wr_state = self.WR_STATE.IDLE
            IFC.READY = 1
          else:
            if ovfl:
              wr_state = self.WR_STATE.WR_HIGH
            else:
              wr_state = self.WR_STATE.IDLE
              IFC.READY = 1

        case self.WR_STATE.WR_HIGH:
          mem[waddr + 1] = out_data[IFC.width: ]
          wr_state = self.WR_STATE.IDLE
          IFC.READY = 1

        case _:
          pass
    else:
      IFC.READY = 0
      wr_state = self.WR_STATE.IDLE


class Test(X.Entity):

  ARGS = dict(clock_frequency=100e6,
              num_tests=50,
              width=32,
              size=4096,
              unit_size=8,
              tdp_ram=False)

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    from . import clock

    CLK = X.mkreg(X.BIT)

    clock.Clock(CLK=CLK,
                frequency=clock_frequency)

    RST_N = X.mkreg(X.BIT)

    self.ifc = RamIfc(CLK, RST_N, width, size,
                      unit_size=unit_size,
                      tdp_ram=tdp_ram)

    Ram(IFC=self.ifc)

  @X.hdl_process(kind=X.INIT_PROCESS)
  def test_run(self):
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
      nunits = random.randint(1, width // unit_size)
      mask = (1 << (nunits * unit_size)) - 1
      value = random.randint(0, mask)

      self.ifc.WREN = nunits
      self.ifc.ADDR = addr
      self.ifc.WDATA = value

      TB.wait_until(CLK, self.ifc.READY == 1)

      self.ifc.WREN = 0
      TB.wait_rising(CLK)

      self.ifc.RDEN = 1

      TB.wait_until(CLK, self.ifc.READY == 1)

      TB.compare_value(self.ifc.RDATA & mask, value,
                       msg=f' : addr={addr}')

      self.ifc.RDEN = 0
      TB.wait_rising(CLK)

    self.ifc.WREN = width // unit_size
    for i in range(num_tests):
      self.ifc.ADDR = i * width // unit_size
      self.ifc.WDATA = i

      TB.wait_rising(CLK)
      TB.wait_until(CLK, self.ifc.READY == 1)

    self.ifc.WREN = 0
    TB.wait_rising(CLK)

    self.ifc.RDEN = 1
    for i in range(num_tests):
      self.ifc.ADDR = i * width // unit_size

      TB.wait_until(CLK, self.ifc.READY == 1)

      TB.compare_value(self.ifc.RDATA, i,
                       msg=f' : addr={i * width // unit_size}')

    self.ifc.RDEN = 0
    TB.wait_rising(CLK)

    XL.finish()

