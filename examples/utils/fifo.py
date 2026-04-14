import py_misc_utils.core_utils as pycu
import py_misc_utils.num_utils as pynu

import pyxhdl as X


class FifoIfc(X.Interface):

  PORT = 'WCLK, WRST_N, RCLK, RRST_N, WUP, RUP, WDATA, =RDATA, =WFULL, =REMPTY'

  def __init__(self, wclk, rclk, wrst_n, rrst_n, width, size):
    addr_size = pynu.address_bits(size)
    fsize = 2**addr_size
    if fsize != size:
      alog.info(f'FIFO size {size} rounded to {fsize} ({width} bits wide)')

    super().__init__('FIFO',
                     width=width,
                     size=fsize,
                     addr_size=addr_size)
    self.mkfield('WCLK', wclk)
    self.mkfield('WRST_N', wrst_n)
    self.mkfield('RCLK', rclk)
    self.mkfield('RRST_N', rrst_n)
    self.mkfield('WUP', X.BIT)
    self.mkfield('RUP', X.BIT)
    self.mkfield('WDATA', X.Bits(width))
    self.mkfield('RDATA', X.Bits(width))
    self.mkfield('WFULL', X.BIT)
    self.mkfield('REMPTY', X.BIT)


class Fifo(X.Entity):

  PORTS = f'*IFC:{__name__}.FifoIfc.PORT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    mem = X.mkreg(X.mkarray(IFC.RDATA.dtype, IFC.size))

    raddr = X.mkwire(X.Uint(IFC.addr_size))
    waddr = X.mkwire(X.Uint(IFC.addr_size))

    rptr = X.mkreg(X.Uint(IFC.addr_size + 1))
    rbin = X.mkreg(X.Uint(IFC.addr_size + 1))
    rptr_sync = X.mkreg(X.Uint(IFC.addr_size + 1))
    rbin_next = X.mkwire(X.Uint(IFC.addr_size + 1))
    rgray_next = X.mkwire(X.Uint(IFC.addr_size + 1))
    rempty_next = X.mkwire(X.BIT)

    wptr = X.mkreg(X.Uint(IFC.addr_size + 1))
    wbin = X.mkreg(X.Uint(IFC.addr_size + 1))
    wptr_sync = X.mkreg(X.Uint(IFC.addr_size + 1))
    wbin_next = X.mkwire(X.Uint(IFC.addr_size + 1))
    wgray_next = X.mkwire(X.Uint(IFC.addr_size + 1))
    wfull_next = X.mkwire(X.BIT)

    rbin_next = rbin + (IFC.RUP & ~IFC.REMPTY)
    rgray_next = (rbin_next >> 1) ^ rbin_next
    rempty_next = (rgray_next == wptr_sync)
    raddr = rbin[: -1]

    wbin_next = wbin + (IFC.WUP & ~IFC.WFULL)
    wgray_next = (wbin_next >> 1) ^ wbin_next
    wfull_next = (wgray_next == (~rptr_sync[-2: ] @ rptr_sync[: -2]))
    waddr = wbin[: -1]

    IFC.RDATA = mem[raddr]

  @X.hdl_process(sens='+IFC.WCLK')
  def mem_write(self):
    if IFC.WUP == 1 and IFC.WFULL == 0:
      mem[waddr] = IFC.WDATA

  @X.hdl_process(sens='+IFC.RCLK')
  def rptr_update(self):
    wptr_s1 = X.mkreg(X.Uint(IFC.addr_size + 1))

    if IFC.RRST_N != 1:
      rbin, rptr, wptr_sync, wptr_s1 = 0, 0, 0, 0
      IFC.REMPTY = 1
    else:
      rbin, rptr = rbin_next, rgray_next
      wptr_sync, wptr_s1 = wptr_s1, wptr
      IFC.REMPTY = rempty_next

  @X.hdl_process(sens='+IFC.WCLK')
  def wptr_update(self):
    rptr_s1 = X.mkreg(X.Uint(IFC.addr_size + 1))

    if IFC.WRST_N != 1:
      wbin, wptr, rptr_sync, rptr_s1 = 0, 0, 0, 0
      IFC.WFULL = 0
    else:
      wbin, wptr = wbin_next, wgray_next
      rptr_sync, rptr_s1 = rptr_s1, rptr
      IFC.WFULL = wfull_next



class Test(X.Entity):

  ARGS = dict(rclock_frequency=100e6,
              wclock_frequency=80e6,
              num_tests=10,
              width=8,
              size=32)

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    from . import clock

    WCLK = X.mkreg(X.BIT)
    RCLK = X.mkreg(X.BIT)

    clock.Clock(CLK=RCLK,
                frequency=rclock_frequency)
    clock.Clock(CLK=WCLK,
                frequency=wclock_frequency)

    RRST_N = X.mkreg(X.BIT)
    WRST_N = X.mkreg(X.BIT)

    self.ifc = FifoIfc(WCLK, WRST_N, RCLK, RRST_N, width, size)

    Fifo(IFC=self.ifc)

  @X.hdl_process(kind=X.INIT_PROCESS)
  def test_run(self):
    import random

    from pyxhdl import xlib as XL
    from pyxhdl import testbench as TB

    WRST_N = 0
    RRST_N = 0

    self.ifc.WUP = 0
    self.ifc.RUP = 0

    TB.wait_rising(RCLK)
    TB.wait_rising(WCLK)

    WRST_N = 1
    RRST_N = 1

    TB.wait_rising(RCLK)
    TB.wait_rising(WCLK)


    XL.finish()

