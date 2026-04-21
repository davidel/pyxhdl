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



// Entity "NestedInterfaceTest" is "NestedInterfaceTest" with:
// 	args={'CLK': 'bits(1)', 'X': 'uint(8)', 'Y': 'uint(8)', 'Q': 'uint(8)'}
// 	kwargs={}
module NestedInterfaceTest(CLK, X, Y, Q);
  input logic CLK;
  input logic [7: 0] X;
  output logic [7: 0] Y;
  output logic [7: 0] Q;
  logic [7: 0] INNER_X;
  logic [7: 0] INNER_Z;
  logic [7: 0] INNER1_X;
  logic [7: 0] INNER1_Z;
  logic [7: 0] OUTER_W;
  NestedIfc NestedIfc_1(
    .CLK(CLK),
    .OIFC_CLK(CLK),
    .IIFCA_CLK(CLK),
    .IIFCA_X(INNER_X),
    .IIFCA_Y(Y),
    .IIFCA_Z(INNER_Z),
    .IIFCB_CLK(CLK),
    .IIFCB_X(INNER1_X),
    .IIFCB_Y(Y),
    .IIFCB_Z(INNER1_Z),
    .OIFC_Q(Q),
    .OIFC_W(OUTER_W)
  );
  assign INNER_X = X + 1;
  assign INNER1_X = X - 1;
endmodule
// Entity "NestedIfc" is "NestedIfc" with:
// 	args={'CLK': 'bits(1)', 'OIFC': 'InterfaceView(an_int:17, CLK:bits(1), IIFCA:InterfaceView(CLK:bits(1), X:uint(8), Y:uint(8), Z:uint(8)), IIFCB:InterfaceView(CLK:bits(1), X:uint(8), Y:uint(8), Z:uint(8)), Q:uint(8), W:uint(8))'}
// 	kwargs={}
module NestedIfc(CLK, OIFC_CLK, IIFCA_CLK, IIFCA_X, IIFCA_Y, IIFCA_Z, IIFCB_CLK, IIFCB_X, IIFCB_Y, IIFCB_Z, OIFC_Q, OIFC_W);
  input logic CLK;
  input logic OIFC_CLK;
  input logic IIFCA_CLK;
  input logic [7: 0] IIFCA_X;
  output logic [7: 0] IIFCA_Y;
  output logic [7: 0] IIFCA_Z;
  input logic IIFCB_CLK;
  input logic [7: 0] IIFCB_X;
  output logic [7: 0] IIFCB_Y;
  output logic [7: 0] IIFCB_Z;
  output logic [7: 0] OIFC_Q;
  output logic [7: 0] OIFC_W;
  always_ff @(posedge CLK)
  nested_process : begin
    OIFC_W <= IIFCA_X + 2;
    IIFCA_Z <= IIFCB_X - 17;
    IIFCB_Y = IIFCA_X % 16;
    OIFC_Q = IIFCB_X + IIFCA_X;
  end
endmodule
