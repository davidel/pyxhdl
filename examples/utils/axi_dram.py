import py_misc_utils.core_utils as pycu
import py_misc_utils.enum as pyen
import py_misc_utils.num_utils as pynu

import pyxhdl as X
from pyxhdl import xlib as XL

from . import axi


class AxiDRAM(X.Entity):

  PORTS = f'*IFC:{__name__}.axi.AxiIfc.SLAVE'

  WSTATE = pyen.make_enum('WSTATE', 'IDLE, DATA, RESP')
  RSTATE = pyen.make_enum('RSTATE', 'IDLE, DATA')

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    ram = X.mkreg(X.mkarray(X.Bits(IFC.data_width), 2**IFC.addr_width))

    wstate = X.mkreg(X.Uint(self.WSTATE._last.bit_length()))
    rstate = X.mkreg(X.Uint(self.RSTATE._last.bit_length()))

    w_addr_reg = X.mkreg(X.Uint(IFC.addr_width))
    r_addr_reg = X.mkreg(X.Uint(IFC.addr_width))
    w_len_reg = X.mkreg(IFC.AWLEN.dtype)
    r_len_reg = X.mkreg(IFC.ARLEN.dtype)

    w_stride = X.mkwire(X.Uint(IFC.addr_width))
    r_stride = X.mkwire(X.Uint(IFC.addr_width))

    bram_din = X.mkwire(IFC.WDATA.dtype)
    bram_dout = X.mkwire(IFC.RDATA.dtype)

    bram_addr = X.mkwire(X.Uint(IFC.addr_width))
    bram_we = X.mkwire(IFC.WSTRB.dtype)
    bram_en = X.mkwire(X.BIT)

    IFC.AWREADY = (wstate == self.WSTATE.IDLE)
    IFC.WREADY = (wstate == self.WSTATE.DATA)

    IFC.ARREADY = (rstate == self.RSTATE.IDLE)

    IFC.RLAST = (rstate == self.RSTATE.DATA and r_len_reg == 0)

    addr_lsb = pynu.address_bits(IFC.data_width // 8)

    w_stride = XL.cast(1, w_stride.dtype) << IFC.AWSIZE
    r_stride = XL.cast(1, r_stride.dtype) << IFC.ARSIZE

    bram_din = IFC.WDATA
    IFC.RDATA = bram_dout

    bram_addr = (w_addr_reg[addr_lsb: -1] if wstate == self.WSTATE.DATA else
                 r_addr_reg[addr_lsb: -1])

    bram_en = ((wstate == self.WSTATE.DATA and IFC.WVALID) or
               (rstate == self.RSTATE.DATA and IFC.RREADY))

    bram_we = IFC.WSTRB if wstate == self.WSTATE.DATA else 0

  @X.hdl_process(sens='+IFC.CLK')
  def wr_fsm(self):
    if IFC.RST_N != 1:
      wstate = self.WSTATE.IDLE
      w_addr_reg = 0
      w_len_reg = 0
      IFC.BVALID = 0
      IFC.BID = 0
      IFC.BRESP = 0
    else:
      match wstate:
        case self.WSTATE.IDLE:
          if IFC.AWVALID:
            w_addr_reg = IFC.AWADDR
            w_len_reg = IFC.AWLEN
            IFC.BID = IFC.AWID
            wstate = self.WSTATE.DATA

        case self.WSTATE.DATA:
          if IFC.WVALID and IFC.WREADY:
            w_addr_reg += w_stride
            if IFC.WLAST:
              IFC.BVALID = 1
              wstate = self.WSTATE.RESP

        case self.WSTATE.RESP:
          if IFC.BREADY:
            IFC.BVALID = 0
            wstate = self.WSTATE.IDLE

        case _:
          pass

  @X.hdl_process(sens='+IFC.CLK')
  def rd_fsm(self):
    if IFC.RST_N != 1:
      rstate = self.RSTATE.IDLE
      r_addr_reg = 0
      r_len_reg = 0
      IFC.RVALID = 0
      IFC.RID = 0
      IFC.RRESP = 0
    else:
      match rstate:
        case self.RSTATE.IDLE:
          if IFC.ARVALID:
            r_addr_reg = IFC.ARADDR
            r_len_reg = IFC.ARLEN
            IFC.RID = IFC.ARID
            IFC.RVALID = 1
            rstate = self.RSTATE.DATA

        case self.RSTATE.DATA:
          if IFC.RVALID and IFC.RREADY:
            if r_len_reg == 0:
              IFC.RVALID = 0
              rstate = self.RSTATE.IDLE
            else:
              r_len_reg -= 1
              r_addr_reg += r_stride

        case _:
          pass

  @X.hdl_process(sens='+IFC.CLK')
  def ram_access(self):
    if bram_en:
      for i in range(IFC.data_width // 8):
        if bram_we[i]:
          ram[bram_addr][i * 8 : (i + 1) * 8] = bram_din[i * 8 : (i + 1) * 8]

      bram_dout = ram[bram_addr]


class AxiBurstIO(X.Entity):

  PORTS = f'*IFC:{__name__}.axi.AxiIfc.MASTER, IOMODE, BURST_LEN, ADDR, WDATA, =RDATA, =DONE'

  STATE = pyen.make_enum('STATE', 'IDLE, WADDR_PHASE, WDATA_PHASE, WRESP_PHASE, ' \
                         'RADDR_PHASE, RDATA_PHASE, DONE')

  MODE = pyen.make_enum('MODE', 'IDLE, RD, WR')

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    state = X.mkreg(X.Uint(self.STATE._last.bit_length()))
    beat_count = X.mkreg(BURST_LEN.dtype)

    IFC.WLAST = (state == self.STATE.WDATA_PHASE and beat_count == IFC.AWLEN)
    IFC.RREADY = (state == self.STATE.RDATA_PHASE)

    IFC.WDATA = WDATA
    RDATA = IFC.RDATA

  @X.hdl_process(sens='+IFC.CLK')
  def io_fsm(self):
    if IFC.RST_N != 1:
      state = self.STATE.IDLE
      beat_count = 0

      # Write signals
      IFC.AWVALID = 0
      IFC.WVALID = 0
      IFC.BREADY = 0
      IFC.AWADDR = 0
      IFC.AWLEN = 0
      IFC.AWSIZE = 0
      IFC.AWBURST = 0
      IFC.AWID = 0
      IFC.WSTRB = 0

      # Read signals.
      IFC.ARVALID = 0
      IFC.ARADDR = 0
      IFC.ARLEN = 0
      IFC.ARSIZE = 0
      IFC.ARBURST = 0
      IFC.ARID = 0

      DONE = 0
    else:
      match state:
        case self.STATE.IDLE:
          DONE = 0

          if IOMODE == self.MODE.RD:
            IFC.ARADDR = ADDR
            IFC.ARLEN = BURST_LEN
            IFC.ARSIZE = (IFC.data_width // 8 - 1).bit_length()
            IFC.ARBURST = 1
            IFC.ARID = 1
            IFC.ARVALID = 1
            state = self.STATE.RADDR_PHASE
          elif IOMODE == self.MODE.WR:
            IFC.AWADDR = ADDR
            IFC.AWLEN = BURST_LEN
            IFC.AWSIZE = (IFC.data_width // 8 - 1).bit_length()
            IFC.AWBURST = 1
            IFC.AWID = 1
            IFC.AWVALID = 1
            state = self.STATE.WADDR_PHASE

        case self.STATE.WADDR_PHASE:
          if IFC.AWREADY:
            IFC.AWVALID = 0
            IFC.WVALID = 1
            IFC.WSTRB = (1 << (IFC.data_width // 8)) - 1
            beat_count = 0
            state = self.STATE.WDATA_PHASE

        case self.STATE.WDATA_PHASE:
          if IFC.WREADY:
            if beat_count == BURST_LEN:
              IFC.WVALID = 0
              IFC.BREADY = 1
              state = self.STATE.WRESP_PHASE
            else:
              beat_count += 1

        case self.STATE.WRESP_PHASE:
          if IFC.BVALID:
            IFC.BREADY = 0
            DONE = 1
            state = self.STATE.DONE

        case self.STATE.RADDR_PHASE:
          if IFC.ARREADY:
            IFC.ARVALID = 0
            state = self.STATE.RDATA_PHASE

        case self.STATE.RDATA_PHASE:
          if IFC.RVALID and IFC.RREADY:
            if IFC.RLAST:
              DONE = 1
              state = self.STATE.DONE

        case self.STATE.DONE:
          DONE = 0
          state = self.STATE.IDLE

        case _:
          pass


class Test(X.Entity):

  ARGS = dict(clock_frequency=100e6,
              num_tests=10,
              data_width=32,
              size=1024) | AxiDRAM.ARGS

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    import py_misc_utils.utils as pyu

    from . import clock

    CLK = X.mkreg(X.BIT)

    clock.Clock(CLK=CLK,
                frequency=clock_frequency)

    RST_N = X.mkreg(X.BIT)

    self.ifc = axi.AxiIfc(CLK=CLK,
                          RST_N=RST_N,
                          data_width=data_width,
                          addr_width=pynu.address_bits(size),
                          strb_width=(data_width + 7) // 8)

    AxiDRAM(IFC=self.ifc,
            **pyu.mget(locals(), *AxiDRAM.ARGS.keys(), as_dict=True))

    IOMODE = X.mkreg(X.Uint(AxiBurstIO.MODE._last.bit_length()))
    BURST_LEN = X.mkreg(X.UINT8)
    ADDR = X.mkreg(X.Bits(self.ifc.addr_width))
    WDATA = X.mkreg(X.Bits(data_width))
    RDATA = X.mkreg(X.Bits(data_width))
    DONE = X.mkreg(X.BIT)

    AxiBurstIO(IFC=self.ifc,
               IOMODE=IOMODE,
               BURST_LEN=BURST_LEN,
               ADDR=ADDR,
               WDATA=WDATA,
               RDATA=RDATA,
               DONE=DONE)

  @X.hdl_process(kind=X.INIT_PROCESS)
  def test_run(self):
    import random

    from pyxhdl import testbench as TB

    RST_N = 0

    TB.wait_rising(CLK)

    RST_N = 1

    for i in range(num_tests):
      count = random.randint(1, 15)
      data = [random.randint(0, 2**self.ifc.data_width - 1) for _ in range(count)]
      addr = random.randint(0, 2**self.ifc.addr_width - 1)

      IOMODE = AxiBurstIO.MODE.WR
      BURST_LEN = count
      ADDR = addr

      WDATA = data[0]
      TB.wait_until(CLK, self.ifc.WREADY == 1)
      TB.wait_rising(CLK)

      for value in data[1: ]:
        WDATA = value
        TB.wait_rising(CLK)

      IOMODE = AxiBurstIO.MODE.IDLE

      TB.wait_until(CLK, DONE == 1)
      TB.wait_rising(CLK)
      TB.wait_until(CLK, DONE == 0)
      TB.wait_rising(CLK)

      IOMODE = AxiBurstIO.MODE.RD

      TB.wait_until(CLK, self.ifc.ARREADY == 1)
      TB.wait_rising(CLK)

      for value in data:
        TB.wait_rising(CLK)
        TB.compare_value(RDATA, value)

      IOMODE = AxiBurstIO.MODE.IDLE

      TB.wait_until(CLK, DONE == 1)
      TB.wait_rising(CLK)
      TB.wait_until(CLK, DONE == 0)
      TB.wait_rising(CLK)

    XL.finish()


UNIT_TESTS = (Test,)

