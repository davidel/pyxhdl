import pyxhdl as X


class AxiIfc(X.Interface):

  AW_FIELDS = ('AWID:u${id_width:4}',
               'AWADDR:u${addr_width}',
               'AWLEN:u8',
               'AWSIZE:u3',
               'AWBURST:u2',
               'AWVALID:bit',
               'AWREADY:bit')

  W_FIELDS = ('WDATA:b${data_width}',
              'WSTRB:b${strb_width:8}',
              'WLAST:bit',
              'WVALID:bit',
              'WREADY:bit')

  B_FIELDS = ('BID:u${id_width:4}',
              'BRESP:u2',
              'BVALID:bit',
              'BREADY:bit')

  AR_FIELDS = ('ARID:u${id_width:4}',
               'ARADDR:u${addr_width}',
               'ARLEN:u8',
               'ARSIZE:u3',
               'ARBURST:u2',
               'ARVALID:bit',
               'ARREADY:bit')

  R_FIELDS = ('RID:u${id_width:4}',
              'RDATA:b${data_width}',
              'RRESP:u2',
              'RLAST:bit',
              'RVALID:bit',
              'RREADY:bit')

  FIELDS = AW_FIELDS + W_FIELDS + B_FIELDS + AR_FIELDS + R_FIELDS

  MASTER = ('CLK, RST_N, AWREADY, WREADY, BID, BRESP, BVALID, ARREADY, RID, RDATA, RRESP, RLAST, RVALID, '
            '=AWID, =AWADDR, =AWLEN, =AWSIZE, =AWBURST, =AWVALID, =WDATA, =WSTRB, =WLAST, '
            '=WVALID, =BREADY, =ARID, =ARADDR, =ARLEN, =ARSIZE, =ARBURST, =ARVALID, =RREADY')

  SLAVE = ('CLK, RST_N, AWID, AWADDR, AWLEN, AWSIZE, AWBURST, AWVALID, WDATA, WSTRB, WLAST, '
           'WVALID, BREADY, ARID, ARADDR, ARLEN, ARSIZE, ARBURST, ARVALID, RREADY, '
           '=AWREADY, =WREADY, =BID, =BRESP, =BVALID, =ARREADY, =RID, =RDATA, =RRESP, =RLAST, =RVALID')

  def __init__(self, **kwargs):
    super().__init__('AXI', **kwargs)

