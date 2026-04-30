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



// Entity "SelectTest" is "SelectTest" with:
// 	args={'A': 'bits(32)', 'XOUT': 'bits(32)'}
// 	kwargs={}
module SelectTest(A, XOUT);
  input logic [31: 0] A;
  output logic [31: 0] XOUT;
  always @(A)
  run : begin
    automatic logic [15: 0] XU_select0;
    automatic logic [15: 0] XU_select1;
    XU_select0[0] = A[0];
    XU_select0[1] = A[2];
    XU_select0[2] = A[4];
    XU_select0[3] = A[6];
    XU_select0[4] = A[8];
    XU_select0[5] = A[10];
    XU_select0[6] = A[12];
    XU_select0[7] = A[14];
    XU_select0[8] = A[16];
    XU_select0[9] = A[18];
    XU_select0[10] = A[20];
    XU_select0[11] = A[22];
    XU_select0[12] = A[24];
    XU_select0[13] = A[26];
    XU_select0[14] = A[28];
    XU_select0[15] = A[30];
    XU_select1[0] = A[1];
    XU_select1[1] = A[3];
    XU_select1[2] = A[5];
    XU_select1[3] = A[7];
    XU_select1[4] = A[9];
    XU_select1[5] = A[11];
    XU_select1[6] = A[13];
    XU_select1[7] = A[15];
    XU_select1[8] = A[17];
    XU_select1[9] = A[19];
    XU_select1[10] = A[21];
    XU_select1[11] = A[23];
    XU_select1[12] = A[25];
    XU_select1[13] = A[27];
    XU_select1[14] = A[29];
    XU_select1[15] = A[31];
    XOUT = {XU_select0, XU_select1};
  end
endmodule
