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

// Entity "InterfaceArrayTest" is "InterfaceArrayTest" with:
// 	args={'CLK': 'bits(1)', 'RST_N': 'bits(1)', 'A': 'uint(2, 8)', 'XOUT': 'uint(2, 8)'}
// 	kwargs={}
module InterfaceArrayTest(CLK, RST_N, A, XOUT);
  input logic CLK;
  input logic RST_N;
  input logic [7: 0] A[2];
  output logic [7: 0] XOUT[2];
  logic [15: 0] MYIFC_X;
  logic [15: 0] MYIFC_Y = unsigned'(16'(0));
  IfcEnt IfcEnt_1(
    .A(A[0]),
    .B(A[1]),
    .IFC_X(MYIFC_X),
    .IFC_Y(MYIFC_Y),
    .IFC_Q(A[0]),
    .IFC_Z(XOUT[0])
  );
  always_ff @(posedge CLK)
  run : begin
    if (&(!RST_N)) begin
      XOUT[1] <= unsigned'(8'(0));
      MYIFC_X <= unsigned'(16'(17));
      MYIFC_Y <= unsigned'(16'(21));
    end else begin
      MYIFC_X <= MYIFC_X - 16'(A[0]);
      MYIFC_Y <= MYIFC_Y + 1;
      XOUT[1] <= 8'(A[0] * 3);
    end
  end
endmodule
// Entity "IfcEnt" is "IfcEnt" with:
// 	args={'A': 'uint(8)', 'B': 'uint(8)', 'IFC': 'InterfaceView(X:uint(16), Y:uint(16), Q:uint(8), Z:uint(8))'}
// 	kwargs={}
module IfcEnt(A, B, IFC_X, IFC_Y, IFC_Q, IFC_Z);
  input logic [7: 0] A;
  input logic [7: 0] B;
  input logic [15: 0] IFC_X;
  input logic [15: 0] IFC_Y;
  input logic [7: 0] IFC_Q;
  output logic [7: 0] IFC_Z;
  always @(A or B or IFC_X or IFC_Y or IFC_Q)
  sensif : begin
    IFC_Z = 8'(16'((A & B) | (A ^ B)) | ((IFC_X + IFC_Y) - 16'(IFC_Q)));
  end
endmodule
