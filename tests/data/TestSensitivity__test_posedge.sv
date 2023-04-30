/* verilator lint_off WIDTH */

`timescale 1 ns / 1 ps

`define MAX(A, B) ((A > B) ? A : B)
`define MIN(A, B) ((A > B) ? B : A)
`define ABS(A) (($signed(A) >= 0) ? A : -$signed(A))
`define FABS(A) ((A >= 0.0) ? A : -A)

`define EXP_OFFSET(NX) (2**(NX - 1) - 1)

// This in theory should be a typedef within the FPU interface, but then
// many HDL tools do not support hierarchical type dereferencing.
`define IEEE754(NX, NM) \
struct packed { \
  logic  sign; \
  logic [NX - 1: 0] exp; \
  logic [NM - 1: 0] mant; \
  }


// PyXHDL support functions.

// Entity "PosEdge" is "PosEdge" with:
// 	args={'CLK': 'bits(1)', 'RESET': 'bits(1)', 'XOUT': 'uint(8)'}
// 	kwargs={}
module PosEdge(CLK, RESET, XOUT);
  input logic CLK;
  input logic RESET;
  output logic [7: 0] XOUT;
  logic [7: 0] XOUT_;
  always @(posedge CLK or RESET)
  run : begin
    if (RESET != unsigned'(1'(0))) begin
      XOUT_ <= unsigned'(8'(0));
    end
  end
  assign XOUT = XOUT_;
endmodule
