import py_misc_utils.core_utils as pycu
import py_misc_utils.num_utils as pynu

import pyxhdl as X


class DClkRamIfc(X.Interface):

  PORT = 'CLK, RST_N, RCLK, REQ, WEN, ADDR, WDATA, =READY, =RDATA'

  def __init__(self, clk, rst_n, rclk, width, size):
    super().__init__('DCLKRAM',
                     width=width,
                     size=size)
    self.mkfield('CLK', clk)
    self.mkfield('RST_N', rst_n)
    self.mkfield('RCLK', rclk)
    self.mkfield('REQ', X.BIT)
    self.mkfield('WEN', X.BIT)
    self.mkfield('ADDR', X.Uint(pynu.address_bits(size)))
    self.mkfield('WDATA', X.Bits(width))
    self.mkfield('READY', X.BIT)
    self.mkfield('RDATA', X.Bits(width))


class DClkRam(X.Entity):

  PORTS = f'*IFC:{__name__}.DClkRamIfc.PORT'
  ARGS = dict(ram_style='block')

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    from . import flopper

    RAM_ATTRS = {
      '$common': {
        'ram_style': ram_style,
      },
    }

    mem = X.mkreg(X.mkarray(IFC.RDATA.dtype, IFC.size),
                  attributes=RAM_ATTRS)
    req_sync = X.mkreg(X.BIT)
    ready_raw = X.mkreg(X.BIT)

    flopper.Flopper(CLK=IFC.RCLK,
                    RST_N=IFC.RST_N,
                    DIN=IFC.REQ,
                    DOUT=req_sync)

    flopper.Flopper(CLK=IFC.CLK,
                    RST_N=IFC.RST_N,
                    DIN=ready_raw,
                    DOUT=IFC.READY)

  @X.hdl_process(sens='+IFC.RCLK')
  def run(self):
    if IFC.RST_N != 1:
      ready_raw = 0
    elif req_sync and ready_raw == 0:
      if IFC.WEN:
        mem[IFC.ADDR] = IFC.WDATA
      else:
        IFC.RDATA = mem[IFC.ADDR]

      ready_raw = 1
    elif req_sync == 0:
      ready_raw = 0


class Test(X.Entity):

  ARGS = dict(cpu_frequency=470e6,
              ram_frequency=100e6,
              num_tests=50,
              width=32,
              size=4096) | DClkRam.ARGS

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    import py_misc_utils.utils as pyu

    from . import clock

    CLK = X.mkreg(X.BIT)

    clock.Clock(CLK=CLK,
                frequency=cpu_frequency)

    RCLK = X.mkreg(X.BIT)

    clock.Clock(CLK=RCLK,
                frequency=ram_frequency)

    RST_N = X.mkreg(X.BIT)

    self.ifc = DClkRamIfc(CLK, RST_N, RCLK, width, size)

    DClkRam(IFC=self.ifc,
            **pyu.mget(locals(), *DClkRam.ARGS.keys(), as_dict=True))

  @X.hdl_process(kind=X.INIT_PROCESS)
  def test_run(self):
    import random

    from pyxhdl import xlib as XL
    from pyxhdl import testbench as TB

    RST_N = 0
    self.ifc.REQ = 0
    self.ifc.WEN = 0
    self.ifc.ADDR = 0
    self.ifc.WDATA = 0

    TB.wait_rising(CLK)
    TB.wait_rising(RCLK)

    RST_N = 1

    TB.wait_rising(CLK)

    for i in range(num_tests):
      addr = random.randint(0, size - 1)
      value = random.randint(0, 2**width - 1)

      self.ifc.REQ = 1
      self.ifc.WEN = 1
      self.ifc.ADDR = addr
      self.ifc.WDATA = value

      TB.wait_until(CLK, self.ifc.READY == 1)

      self.ifc.REQ = 0
      self.ifc.WEN = 0
      TB.wait_rising(CLK)
      TB.wait_until(CLK, self.ifc.READY == 0)

      self.ifc.REQ = 1

      TB.wait_until(CLK, self.ifc.READY == 1)

      TB.compare_value(self.ifc.RDATA, value,
                       msg=f' : addr={addr}')

      self.ifc.REQ = 0
      TB.wait_rising(CLK)
      TB.wait_until(CLK, self.ifc.READY == 0)

    XL.finish()

