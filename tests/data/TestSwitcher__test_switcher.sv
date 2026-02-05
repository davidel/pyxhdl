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



// Entity "Switcher" is "Switcher" with:
// 	args={'SEL': 'bits(3)', 'DIN': 'bits(16)', 'SEL_DOUT': 'bits(8, 16)', 'SEL_DIN': 'bits(8, 16)', 'DOUT': 'bits(16)'}
// 	kwargs={}
module Switcher(SEL, DIN, SEL_DOUT, SEL_DIN, DOUT);
  input logic [2: 0] SEL;
  input logic [15: 0] DIN;
  output logic [15: 0] SEL_DOUT[8];
  input logic [15: 0] SEL_DIN[8];
  output logic [15: 0] DOUT;
  always_comb
  switch : begin
    SEL_DOUT = '{8{16'bxxxxxxxxxxxxxxxx}};
    DOUT = 16'bxxxxxxxxxxxxxxxx;
    if (SEL == unsigned'(3'(0))) begin
      SEL_DOUT[0] = DIN;
      DOUT = SEL_DIN[0];
    end
    if (SEL == unsigned'(3'(1))) begin
      SEL_DOUT[1] = DIN;
      DOUT = SEL_DIN[1];
    end
    if (SEL == unsigned'(3'(2))) begin
      SEL_DOUT[2] = DIN;
      DOUT = SEL_DIN[2];
    end
    if (SEL == unsigned'(3'(3))) begin
      SEL_DOUT[3] = DIN;
      DOUT = SEL_DIN[3];
    end
    if (SEL == unsigned'(3'(4))) begin
      SEL_DOUT[4] = DIN;
      DOUT = SEL_DIN[4];
    end
    if (SEL == unsigned'(3'(5))) begin
      SEL_DOUT[5] = DIN;
      DOUT = SEL_DIN[5];
    end
    if (SEL == unsigned'(3'(6))) begin
      SEL_DOUT[6] = DIN;
      DOUT = SEL_DIN[6];
    end
    if (SEL == unsigned'(3'(7))) begin
      SEL_DOUT[7] = DIN;
      DOUT = SEL_DIN[7];
    end
  end
endmodule
