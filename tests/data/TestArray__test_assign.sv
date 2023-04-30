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

// Entity "ArrayAssignTestEnt" is "ArrayAssignTestEnt" with:
// 	args={'A': 'uint(2, 2, 16)', 'B': 'sint(2, 2, 16)', 'XOUT': 'sint(2, 2, 16)'}
// 	kwargs={}
module ArrayAssignTestEnt(A, B, XOUT);
  input logic [15: 0] A[2][2];
  input logic signed [15: 0] B[2][2];
  output logic signed [15: 0] XOUT[2][2];
  logic signed [15: 0] XOUT_[2][2];
  always @(A or B)
  assign_element : begin
    XOUT_[1] = B[0];
  end
  assign XOUT = XOUT_;
endmodule
