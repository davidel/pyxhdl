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

// Entity "BasicBool" is "BasicBool" with:
// 	args={'A': 'bool()', 'B': 'bool()', 'C': 'uint(8)', 'XOUT': 'bool()'}
// 	kwargs={}
module BasicBool(A, B, C, XOUT);
  input logic A;
  input logic B;
  input logic [7: 0] C;
  output logic XOUT;
  wire logic [3: 0] xx;
  logic XOUT_;
  logic [3: 0] xx_ = 4'b1001;
  always @(A or B or C)
  run : begin
    logic [7: 0] cc;
    if (xx == 4'(A)) begin
      cc = C - 3;
    end else begin
      cc = C + 17;
    end
    XOUT_ = (A && B) || (cc > unsigned'(8'(10)));
  end
  assign XOUT = XOUT_;
  assign xx = xx_;
endmodule
