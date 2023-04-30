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


module ExEntity(IN_A, IN_B, OUT_DATA);
  parameter integer NBITS = 8;
  parameter integer DELTA = 16;

  input logic [NBITS - 1: 0] IN_A;
  input logic [NBITS - 1: 0] IN_B;
  output logic [NBITS - 1: 0] OUT_DATA;

  assign OUT_DATA = IN_A + IN_B - DELTA;
endmodule

// Entity "PlaceEntity" is "PlaceEntity" with:
// 	args={'A': 'uint(8)', 'B': 'uint(8)', 'XOUT': 'uint(8)'}
// 	kwargs={}
module PlaceEntity(A, B, XOUT);
  input logic [7: 0] A;
  input logic [7: 0] B;
  output logic [7: 0] XOUT;
  ExEntity #(.NBITS(8), .DELTA(7)) ExEntity_1(
    .IN_A(A),
    .IN_B(B),
    .OUT_DATA(XOUT)
  );
endmodule
