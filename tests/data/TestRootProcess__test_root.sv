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

// Entity "RootProcess" is "RootProcess" with:
// 	args={'A': 'uint(8)', 'B': 'uint(8)', 'XOUT': 'uint(8)'}
// 	kwargs={}
module RootProcess(A, B, XOUT);
  input logic [7: 0] A;
  input logic [7: 0] B;
  output logic [7: 0] XOUT;
  wire logic [7: 0] temp;
  logic [7: 0] temp_ = unsigned'(8'(21));
  assign XOUT = (A - 8'(3 * B)) - temp;
  assign temp = temp_;
endmodule
