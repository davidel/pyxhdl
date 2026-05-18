import pyxhdl as X


class AxiIfc(X.Interface):

  AW_FIELDS = ('AWID:u${id_width}',
               'AWADDR:u${addr_width}',
               'AWLEN:u8',
               'AWSIZE:u3',
               'AWBURST:u2',
               'AWVALID:bit',
               'AWREADY:bit')

  W_FIELDS = ('WDATA:b${data_width}',
              'WSTRB:b${strb_width}',
              'WLAST:bit',
              'WVALID:bit',
              'WREADY:bit')

  B_FIELDS = ('BID:u${id_width}',
              'BRESP:u2',
              'BVALID:bit',
              'BREADY:bit')

  AR_FIELDS = ('ARID:u${id_width}',
               'ARADDR:u${addr_width}',
               'ARLEN:u8',
               'ARSIZE:u3',
               'ARBURST:u2',
               'ARVALID:bit',
               'ARREADY:bit')

  R_FIELDS = ('RID:u${id_width}',
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

  def __init__(self,
               id_width=4,
               strb_width=8,
               **kwargs):
    super().__init__('AXI',
                     id_width=id_width,
                     strb_width=strb_width,
                     **kwargs)

