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

// Entity "Recast" is "Recast" with:
// 	args={'A': 'uint(8)', 'B': 'uint(8)', 'XOUT': 'uint(4)'}
// 	kwargs={}
module Recast(A, B, XOUT);
  input logic [7: 0] A;
  input logic [7: 0] B;
  output logic [3: 0] XOUT;
  logic [3: 0] XOUT_;
  always @(A or B)
  run : begin
    logic [7: 0] auto;
    auto = A + B;
    auto = 8'(A * B);
    XOUT_ = 4'(auto / 4);
  end
  assign XOUT = XOUT_;
endmodule
