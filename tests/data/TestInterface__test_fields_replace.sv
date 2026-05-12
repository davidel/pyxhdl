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



// Entity "FieldsReplaceInterfaceTest" is "FieldsReplaceInterfaceTest" with:
// 	args={'CLK': 'bits(1)', 'A': 'uint(15)', 'XOUT': 'uint(15)'}
// 	kwargs={}
module FieldsReplaceInterfaceTest(CLK, A, XOUT);
  input logic CLK;
  input logic [14: 0] A;
  output logic [14: 0] XOUT;
  logic [14: 0] FREPL_RF;
  always_ff @(posedge CLK)
  clk_proc : begin
    if (A == 15'd0) begin
      FREPL_RF <= 15'd0;
    end else begin
      XOUT <= A + FREPL_RF;
      FREPL_RF <= FREPL_RF + 1;
    end
  end
endmodule
