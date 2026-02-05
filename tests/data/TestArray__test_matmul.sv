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

package pyxhdl;

  function automatic bit float_equal(real value, real ref_value, real eps);
    real toll = fp::MAX(fp::FABS(value), fp::FABS(ref_value)) * eps;

    begin
      float_equal = (fp::FABS(value - ref_value) < toll) ? 1'b1 : 1'b0;
    end
  endfunction
endpackage



// Entity "MatMult" is "MatMult" with:
// 	args={'A': 'uint(4, 4, 16)', 'B': 'uint(4, 4, 16)', 'XOUT': 'uint(4, 4, 16)'}
// 	kwargs={}
module MatMult(A, B, XOUT);
  input logic [15: 0] A[4][4];
  input logic [15: 0] B[4][4];
  output logic [15: 0] XOUT[4][4];
  always @(A or B)
  mat_mult : begin
    XOUT[0][0] = (((0 + 16'(A[0][0] * B[0][0])) + 16'(A[0][1] * B[1][0])) + 16'(A[0][2] * B[2][0])) + 16'(A[0][3] * B[3][0]);
    XOUT[0][1] = (((0 + 16'(A[0][0] * B[0][1])) + 16'(A[0][1] * B[1][1])) + 16'(A[0][2] * B[2][1])) + 16'(A[0][3] * B[3][1]);
    XOUT[0][2] = (((0 + 16'(A[0][0] * B[0][2])) + 16'(A[0][1] * B[1][2])) + 16'(A[0][2] * B[2][2])) + 16'(A[0][3] * B[3][2]);
    XOUT[0][3] = (((0 + 16'(A[0][0] * B[0][3])) + 16'(A[0][1] * B[1][3])) + 16'(A[0][2] * B[2][3])) + 16'(A[0][3] * B[3][3]);
    XOUT[1][0] = (((0 + 16'(A[1][0] * B[0][0])) + 16'(A[1][1] * B[1][0])) + 16'(A[1][2] * B[2][0])) + 16'(A[1][3] * B[3][0]);
    XOUT[1][1] = (((0 + 16'(A[1][0] * B[0][1])) + 16'(A[1][1] * B[1][1])) + 16'(A[1][2] * B[2][1])) + 16'(A[1][3] * B[3][1]);
    XOUT[1][2] = (((0 + 16'(A[1][0] * B[0][2])) + 16'(A[1][1] * B[1][2])) + 16'(A[1][2] * B[2][2])) + 16'(A[1][3] * B[3][2]);
    XOUT[1][3] = (((0 + 16'(A[1][0] * B[0][3])) + 16'(A[1][1] * B[1][3])) + 16'(A[1][2] * B[2][3])) + 16'(A[1][3] * B[3][3]);
    XOUT[2][0] = (((0 + 16'(A[2][0] * B[0][0])) + 16'(A[2][1] * B[1][0])) + 16'(A[2][2] * B[2][0])) + 16'(A[2][3] * B[3][0]);
    XOUT[2][1] = (((0 + 16'(A[2][0] * B[0][1])) + 16'(A[2][1] * B[1][1])) + 16'(A[2][2] * B[2][1])) + 16'(A[2][3] * B[3][1]);
    XOUT[2][2] = (((0 + 16'(A[2][0] * B[0][2])) + 16'(A[2][1] * B[1][2])) + 16'(A[2][2] * B[2][2])) + 16'(A[2][3] * B[3][2]);
    XOUT[2][3] = (((0 + 16'(A[2][0] * B[0][3])) + 16'(A[2][1] * B[1][3])) + 16'(A[2][2] * B[2][3])) + 16'(A[2][3] * B[3][3]);
    XOUT[3][0] = (((0 + 16'(A[3][0] * B[0][0])) + 16'(A[3][1] * B[1][0])) + 16'(A[3][2] * B[2][0])) + 16'(A[3][3] * B[3][0]);
    XOUT[3][1] = (((0 + 16'(A[3][0] * B[0][1])) + 16'(A[3][1] * B[1][1])) + 16'(A[3][2] * B[2][1])) + 16'(A[3][3] * B[3][1]);
    XOUT[3][2] = (((0 + 16'(A[3][0] * B[0][2])) + 16'(A[3][1] * B[1][2])) + 16'(A[3][2] * B[2][2])) + 16'(A[3][3] * B[3][2]);
    XOUT[3][3] = (((0 + 16'(A[3][0] * B[0][3])) + 16'(A[3][1] * B[1][3])) + 16'(A[3][2] * B[2][3])) + 16'(A[3][3] * B[3][3]);
  end
endmodule
