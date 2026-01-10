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

// Entity "MatchEnt" is "MatchEnt" with:
// 	args={'A': 'uint(8)', 'B': 'uint(8)', 'XOUT': 'uint(8)'}
// 	kwargs={}
module MatchEnt(A, B, XOUT);
  input logic [7: 0] A;
  input logic [7: 0] B;
  output logic [7: 0] XOUT;
  logic [7: 0] XOUT_;
  always @(A or B)
  tester : begin
    case (A)
      unsigned'(8'(17)):
        XOUT_ = A + 1;
      unsigned'(8'(21)):
        XOUT_ = A + B;
      unsigned'(8'(34)):
        XOUT_ = A - B;
      default:
        XOUT_ = 8'(A * B);
    endcase
  end
  assign XOUT = XOUT_;
endmodule
