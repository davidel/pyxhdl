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



// Entity "BasicBits" is "BasicBits" with:
// 	args={'A': 'bits(1)', 'B': 'bits(1)', 'XOUT': 'bits(4)'}
// 	kwargs={}
module BasicBits(A, B, XOUT);
  input logic A;
  input logic B;
  output logic [3: 0] XOUT;
  logic [3: 0] z;
  always @(A or B)
  run : begin
    automatic logic [3: 0] w;
    z = 4'((2'(A) + 2'(B)) + 3);
    w = z;
    XOUT = 4'(z * 17) - w;
  end
endmodule
