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

// Entity "BasicBits" is "BasicBits" with:
// 	args={'A': 'bits(1)', 'B': 'bits(1)', 'XOUT': 'bits(4)'}
// 	kwargs={}
module BasicBits(A, B, XOUT);
  input logic A;
  input logic B;
  output logic [3: 0] XOUT;
  wire logic [3: 0] w;
  logic [3: 0] w_;
  logic [3: 0] XOUT_;
  always @(A or B)
  run : begin
    logic [3: 0] z;
    z = 4'((2'(A) + 2'(B)) + 3);
    w_ = z;
    XOUT_ = 4'(z * 17) - w;
  end
  assign w = w_;
  assign XOUT = XOUT_;
endmodule
