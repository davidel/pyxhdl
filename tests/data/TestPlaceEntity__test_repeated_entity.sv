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



// Entity "RepeatFew" is "RepeatFew" with:
// 	args={'A': 'uint(8)', 'B': 'uint(16)', 'XOUT1': 'uint(8)', 'XOUT2': 'uint(8)'}
// 	kwargs={}
module RepeatFew(A, B, XOUT1, XOUT2);
  input logic [7: 0] A;
  input logic [15: 0] B;
  output logic [7: 0] XOUT1;
  output logic [7: 0] XOUT2;
  Repeated Repeated_1(
    .A(A),
    .B(B),
    .XOUT(XOUT1)
  );
  Repeated_V1 Repeated_V1_1(
    .A(B),
    .B(A),
    .XOUT(XOUT2)
  );
endmodule
// Entity "Repeated" is "Repeated" with:
// 	args={'A': 'uint(8)', 'B': 'uint(16)', 'XOUT': 'uint(8)'}
// 	kwargs={index=17}
module Repeated(A, B, XOUT);
  input logic [7: 0] A;
  input logic [15: 0] B;
  output logic [7: 0] XOUT;
  always @(A or B)
  run : begin
    XOUT = 8'((16'(A) + B) - 17);
  end
endmodule
// Entity "Repeated_V1" is "Repeated" with:
// 	args={'A': 'uint(16)', 'B': 'uint(8)', 'XOUT': 'uint(8)'}
// 	kwargs={index=21}
module Repeated_V1(A, B, XOUT);
  input logic [15: 0] A;
  input logic [7: 0] B;
  output logic [7: 0] XOUT;
  always @(A or B)
  run : begin
    XOUT = 8'((A + 16'(B)) - 21);
  end
endmodule
