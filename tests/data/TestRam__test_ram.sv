/* verilator lint_off WIDTH */

`timescale 1 ns / 100 ps


package fp;
  let MAX(A, B) = ((A > B) ? A : B);
  let MIN(A, B) = ((A > B) ? B : A);
  let ABS(A) = (($signed(A) >= 0) ? A : -$signed(A));
  let FABS(A) = ((A >= 0.0) ? A : -A);

  let EXP_OFFSET(NX) = (2**(NX - 1) - 1);
endpackage

// This in theory should be a typedef within the FPU interface, but then
// many HDL tools do not support hierarchical type dereferencing.
`define IEEE754(NX, NM) \
struct packed { \
  logic  sign; \
  logic [NX - 1: 0] exp; \
  logic [NM - 1: 0] mant; \
  }


// PyXHDL support functions.

// Entity "RamTest" is "RamTest" with:
// 	args={'CLK': 'bits(1)', 'RST_N': 'bits(1)', 'RDEN': 'bits(1)', 'WREN': 'bits(1)', 'ADDR': 'bits(12)', 'IN_DATA': 'bits(16)', 'OUT_DATA': 'bits(16)'}
// 	kwargs={RAM_SIZE=3072}
module RamTest(CLK, RST_N, RDEN, WREN, ADDR, IN_DATA, OUT_DATA);
  input logic CLK;
  input logic RST_N;
  input logic RDEN;
  input logic WREN;
  input logic [11: 0] ADDR;
  input logic [15: 0] IN_DATA;
  output logic [15: 0] OUT_DATA;
  logic [15: 0] mem[3072];
  always_ff @(posedge CLK)
  run : begin
    if (&(!RST_N)) begin
      OUT_DATA <= unsigned'(16'(0));
    end else if (&WREN) begin
      mem[int'(ADDR)] <= IN_DATA;
    end else if (&RDEN) begin
      OUT_DATA <= mem[int'(ADDR)];
    end
  end
endmodule
