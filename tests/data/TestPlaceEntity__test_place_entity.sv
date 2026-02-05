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




module ExEntity(IN_A, IN_B, OUT_DATA);
  parameter integer NBITS = 8;
  parameter integer DELTA = 16;

  input logic [NBITS - 1: 0] IN_A;
  input logic [NBITS - 1: 0] IN_B;
  output logic [NBITS - 1: 0] OUT_DATA;

  assign OUT_DATA = IN_A + IN_B - DELTA;
endmodule

// Entity "PlaceEntity" is "PlaceEntity" with:
// 	args={'A': 'uint(8)', 'B': 'uint(8)', 'XOUT': 'uint(8)'}
// 	kwargs={}
module PlaceEntity(A, B, XOUT);
  input logic [7: 0] A;
  input logic [7: 0] B;
  output logic [7: 0] XOUT;
  ExEntity #(.NBITS(8), .DELTA(7)) ExEntity_1(
    .IN_A(A),
    .IN_B(B),
    .OUT_DATA(XOUT)
  );
endmodule
