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



// Entity "NetsTest" is "NetsTest" with:
// 	args={'CLK': 'bits(1)', 'A': 'uint(8)', 'B': 'uint(8)', 'XOUT': 'uint(8)'}
// 	kwargs={}
module NetsTest(CLK, A, B, XOUT);
  input logic CLK;
  input logic [7: 0] A;
  input logic [7: 0] B;
  output logic [7: 0] XOUT;
  logic [7: 0] ROOT_REG;
  logic [7: 0] ROOT_WIRE;
  assign ROOT_WIRE = 8'(A * B);
  always @(A or B)
  combo : begin
    automatic logic [7: 0] COMBO_WIRE;
    if (A > B) begin
      COMBO_WIRE = (A + B) - ROOT_WIRE;
    end else begin
      COMBO_WIRE = (A - B) + ROOT_WIRE;
    end
    ROOT_REG = COMBO_WIRE;
  end
  always_ff @(posedge CLK)
  clocker : begin
    if (B == 8'(1)) begin
      XOUT = ROOT_REG;
    end
  end
endmodule
