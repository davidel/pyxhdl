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

// Entity "ArrayVarSliceEnt" is "ArrayVarSliceEnt" with:
// 	args={'A': 'uint(32)', 'B': 'uint(4)', 'XOUT': 'bits(4)'}
// 	kwargs={}
module ArrayVarSliceEnt(A, B, XOUT);
  input logic [31: 0] A;
  input logic [3: 0] B;
  output logic [3: 0] XOUT;
  always @(A or B)
  var_slice : begin
    XOUT = A[int'(B + 1) -: 4];
  end
endmodule
