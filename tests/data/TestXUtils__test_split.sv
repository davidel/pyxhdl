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



// Entity "SplitTest" is "SplitTest" with:
// 	args={'A': 'bits(32)', 'XOUT': 'bits(32)'}
// 	kwargs={}
module SplitTest(A, XOUT);
  input logic [31: 0] A;
  output logic [31: 0] XOUT;
  always @(A)
  run : begin
    automatic logic [3: 0] XU_split0;
    automatic logic [4: 0] XU_split1;
    automatic logic [21: 0] XU_split2;
    XU_split0 = A[4: 1];
    XU_split1 = A[9: 5];
    XU_split2 = A[31: 10];
    XOUT = 32'({{XU_split2, XU_split0}, XU_split1});
  end
endmodule
