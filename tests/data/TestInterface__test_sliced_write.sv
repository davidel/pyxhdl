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



// Entity "SlicedWriteInterfaceTest" is "SlicedWriteInterfaceTest" with:
// 	args={'CLK': 'bits(1)', 'A': 'uint(15)', 'B': 'uint(15)', 'XOUT': 'uint(15)'}
// 	kwargs={}
module SlicedWriteInterfaceTest(CLK, A, B, XOUT);
  input logic CLK;
  input logic [14: 0] A;
  input logic [14: 0] B;
  output logic [14: 0] XOUT;
  SliceWriteIfc SliceWriteIfc_1(
    .CLK(CLK),
    .A(A[3: 0]),
    .B(B[3: 0]),
    .XOUT(XOUT[3: 0])
  );
  SliceWriteIfc SliceWriteIfc_2(
    .CLK(CLK),
    .A(A[7: 4]),
    .B(B[7: 4]),
    .XOUT(XOUT[7: 4])
  );
  SliceWriteIfc SliceWriteIfc_3(
    .CLK(CLK),
    .A(A[11: 8]),
    .B(B[11: 8]),
    .XOUT(XOUT[11: 8])
  );
  SliceWriteIfc_V1 SliceWriteIfc_V1_1(
    .CLK(CLK),
    .A(A[14: 12]),
    .B(B[14: 12]),
    .XOUT(XOUT[14: 12])
  );
endmodule
// Entity "SliceWriteIfc" is "SliceWriteIfc" with:
// 	args={'CLK': 'bits(1)', 'A': 'uint(4)', 'B': 'uint(4)', 'XOUT': 'uint(4)'}
// 	kwargs={}
module SliceWriteIfc(CLK, A, B, XOUT);
  input logic CLK;
  input logic [3: 0] A;
  input logic [3: 0] B;
  output logic [3: 0] XOUT;
  always_ff @(posedge CLK)
  writeit : begin
    XOUT <= A + B;
  end
endmodule
// Entity "SliceWriteIfc_V1" is "SliceWriteIfc" with:
// 	args={'CLK': 'bits(1)', 'A': 'uint(3)', 'B': 'uint(3)', 'XOUT': 'uint(3)'}
// 	kwargs={}
module SliceWriteIfc_V1(CLK, A, B, XOUT);
  input logic CLK;
  input logic [2: 0] A;
  input logic [2: 0] B;
  output logic [2: 0] XOUT;
  always_ff @(posedge CLK)
  writeit : begin
    XOUT <= A + B;
  end
endmodule
