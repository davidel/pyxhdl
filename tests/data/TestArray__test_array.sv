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



// Entity "ArrayTestEnt" is "ArrayTestEnt" with:
// 	args={'A': 'uint(2, 2, 16)', 'B': 'uint(2, 2, 16)', 'XOUT': 'uint(16)'}
// 	kwargs={}
module ArrayTestEnt(A, B, XOUT);
  input logic [15: 0] A[2][2];
  input logic [15: 0] B[2][2];
  output logic [15: 0] XOUT;
  logic [15: 0] ar[3][2][4] = {{{16'(0), 16'(1), 16'(2), 16'(3)}, {16'(4), 16'(5), 16'(6), 16'(7)}}, {{16'(8), 16'(9), 16'(10), 16'(11)}, {16'(12), 16'(13), 16'(14), 16'(15)}}, {{16'(16), 16'(17), 16'(18), 16'(19)}, {16'(20), 16'(21), 16'(22), 16'(23)}}};
  const logic [15: 0] ar_const[3][2][4] = {{{16'(0), 16'(1), 16'(2), 16'(3)}, {16'(4), 16'(5), 16'(6), 16'(7)}}, {{16'(8), 16'(9), 16'(10), 16'(11)}, {16'(12), 16'(13), 16'(14), 16'(15)}}, {{16'(16), 16'(17), 16'(18), 16'(19)}, {16'(20), 16'(21), 16'(22), 16'(23)}}};
  always @(A or B)
  slicing : begin
    XOUT = 16'(A[1][0][7: 4] + B[0][1][3: 0]);
  end
  always @(A or B)
  assign_slicing : begin
    XOUT[3: 0] = A[1][0][7: 4];
    XOUT[7: 4] = B[0][1][3: 0];
  end
  always @(A or B)
  indexing : begin
    XOUT = B[0][int'(A[0][1])];
  end
  always @(A or B)
  np_init : begin
    XOUT = (B[0][1] - ar[1][0][1]) + ar_const[2][1][2];
  end
endmodule
