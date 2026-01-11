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

// Entity "RealEnt" is "RealEnt" with:
// 	args={'A': 'real()', 'B': 'real()', 'XOUT': 'real()'}
// 	kwargs={}
module RealEnt(A, B, XOUT);
  input real A;
  input real B;
  output real XOUT;
  real add;
  real mul;
  real div;
  real sub;
  always @(A or B)
  run : begin
    add = A + B;
    mul = A * B;
    div = A / B;
    sub = A - B;
    XOUT = ((add + mul) - div) + (sub * ((A + 3.0) - (A + 3.12)));
  end
endmodule
