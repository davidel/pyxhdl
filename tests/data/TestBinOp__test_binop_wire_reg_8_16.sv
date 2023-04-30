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

// Entity "BinOp" is "BinOp" with:
// 	args={'A': 'uint(8)', 'B': 'uint(16)', 'XOUT': 'uint(16)'}
// 	kwargs={}
module BinOp(A, B, XOUT);
  input logic [7: 0] A;
  input logic [15: 0] B;
  output logic [15: 0] XOUT;
  logic [15: 0] XOUT_;
  always @(A or B)
  run : begin
    logic [7: 0] add;
    logic [7: 0] mul;
    logic [7: 0] div;
    logic [7: 0] sub;
    add = 8'(16'(A) + B);
    mul = 8'(16'(16'(A) * B));
    div = 8'(16'(A) / B);
    sub = 8'(16'(A) - B);
    XOUT_ = 16'((24'(16'(((add + mul) - div) + sub) - (16'(A) % B)) + {A, B}) - (({A, B} << 6) ^ ({A, B} >> 6)));
  end
  assign XOUT = XOUT_;
endmodule
