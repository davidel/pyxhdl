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



// Entity "IfEnt" is "IfEnt" with:
// 	args={'A': 'uint(8)', 'B': 'uint(8)', 'XOUT': 'uint(8)'}
// 	kwargs={kwarg=17}
module IfEnt(A, B, XOUT);
  input logic [7: 0] A;
  input logic [7: 0] B;
  output logic [7: 0] XOUT;
  always @(A or B)
  run : begin
    automatic logic [7: 0] temp;
    temp = A;
    if (A > B) begin
      temp = temp + A;
    end else if (B > A) begin
      temp = temp - B;
    end else if (B == A) begin
      temp = 8'(temp * B);
    end else begin
      temp = 8'(0);
    end
    if (A > B) begin
      temp = temp - A;
    end else if (A < B) begin
      temp = temp + A;
    end else begin
      if (A == B) begin
        temp = temp / A;
      end
      temp = temp + 1;
    end
    if (A > B) begin
      temp = temp - 1;
    end
    // You should always see this: 17 <= 1000
    temp = temp + 17;
    XOUT = temp;
  end
endmodule
