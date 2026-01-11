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

// Entity "IntReal" is "IntReal" with:
// 	args={'A': 'integer()', 'B': 'real()', 'XOUT': 'real(4)'}
// 	kwargs={}
module IntReal(A, B, XOUT);
  input integer A;
  input real B;
  output real XOUT[4];
  integer idx = 3;
  always @(A)
  test : begin
    XOUT[idx] = ((real'(A) + B) * 17.0) - 3.14;
    idx = idx - 1;
    XOUT[idx] = ((real'(A) + B) / 21.0) + 2.718281828459045;
    idx = idx - 1;
    XOUT[idx] = (real'(A) + B) + real'(idx);
  end
endmodule
