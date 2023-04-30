/* verilator lint_off WIDTH */

`timescale 1 ns / 1 ps

`define MAX(A, B) ((A > B) ? A : B)
`define MIN(A, B) ((A > B) ? B : A)
`define ABS(A) (($signed(A) >= 0) ? A : -$signed(A))
`define FABS(A) ((A >= 0.0) ? A : -A)

`define EXP_OFFSET(NX) (2**(NX - 1) - 1)

// This in theory should be a typedef within the FPU interface, but then
// many HDL tools do not support hierarchical type dereferencing.
`define IEEE754(NX, NM) \
struct packed { \
  logic  sign; \
  logic [NX - 1: 0] exp; \
  logic [NM - 1: 0] mant; \
  }


// PyXHDL support functions.

// Entity "IfEnt" is "IfEnt" with:
// 	args={'A': 'uint(8)', 'B': 'uint(16)', 'XOUT': 'uint(16)'}
// 	kwargs={kwarg: 3}
module IfEnt(A, B, XOUT);
  input logic [7: 0] A;
  input logic [15: 0] B;
  output logic [15: 0] XOUT;
  logic [15: 0] XOUT_;
  always @(A or B)
  run : begin
    logic [7: 0] temp;
    temp = 8'(B);
    if (16'(A) > B) begin
      temp = temp + A;
    end else if (B > 16'(A)) begin
      temp = 8'(16'(temp) - B);
    end else if (B == 16'(A)) begin
      temp = 8'(16'(16'(temp) * B));
    end else begin
      temp = unsigned'(8'(0));
    end
    if (16'(A) > B) begin
      temp = temp - A;
    end else if (16'(A) < B) begin
      temp = temp + A;
    end else begin
      if (16'(A) == B) begin
        temp = temp / A;
      end
      temp = temp + 1;
    end
    XOUT_ = 16'(temp);
  end
  assign XOUT = XOUT_;
endmodule
