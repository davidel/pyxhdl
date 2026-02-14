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



// Entity "BasicBool" is "BasicBool" with:
// 	args={'A': 'bool()', 'B': 'bool()', 'C': 'uint(8)', 'XOUT': 'bool()'}
// 	kwargs={}
module BasicBool(A, B, C, XOUT);
  input logic A;
  input logic B;
  input logic [7: 0] C;
  output logic XOUT;
  logic [7: 0] cc;
  always @(A or B or C)
  run : begin
    static logic [3: 0] xx = 4'b1001;
    if (xx == 4'(A)) begin
      cc = C - 3;
    end else begin
      cc = C + 17;
    end
    XOUT = (A && B) || (cc > 8'(10));
  end
endmodule
