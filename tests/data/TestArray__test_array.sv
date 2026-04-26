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
  logic [15: 0] ar[3][2][4] = {{{16'd0, 16'd1, 16'd2, 16'd3}, {16'd4, 16'd5, 16'd6, 16'd7}}, {{16'd8, 16'd9, 16'd10, 16'd11}, {16'd12, 16'd13, 16'd14, 16'd15}}, {{16'd16, 16'd17, 16'd18, 16'd19}, {16'd20, 16'd21, 16'd22, 16'd23}}};
  const logic [15: 0] ar_const[3][2][4] = {{{16'd0, 16'd1, 16'd2, 16'd3}, {16'd4, 16'd5, 16'd6, 16'd7}}, {{16'd8, 16'd9, 16'd10, 16'd11}, {16'd12, 16'd13, 16'd14, 16'd15}}, {{16'd16, 16'd17, 16'd18, 16'd19}, {16'd20, 16'd21, 16'd22, 16'd23}}};
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
