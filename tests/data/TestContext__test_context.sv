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

// Entity "ContextEnt" is "ContextEnt" with:
// 	args={'A': 'uint(8)', 'B': 'uint(8)', 'XOUT': 'uint(8)'}
// 	kwargs={}
module ContextEnt(A, B, XOUT);
  input logic [7: 0] A;
  input logic [7: 0] B;
  output logic [7: 0] XOUT;
  wire logic [7: 0] c;
  wire logic [7: 0] d;
  logic [7: 0] c_;
  logic [7: 0] d_;
  logic [7: 0] XOUT_;
  always @(A or B)
  tester : begin
    #10 c_ = A - B;
    #17 d_ = d + (A / B);
    XOUT_ = c + 8'(A * B);
  end
  assign c = c_;
  assign d = d_;
  assign XOUT = XOUT_;
endmodule
