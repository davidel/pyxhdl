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

// Entity "AttributesTest" is "AttributesTest" with:
// 	args={'A': 'uint(8)', 'B': 'uint(8)', 'XOUT': 'uint(8)'}
// 	kwargs={}
module AttributesTest(A, B, XOUT);
  input logic [7: 0] A;
  input logic [7: 0] B;
  output logic [7: 0] XOUT;
  always @(A or B)
  run : begin
    (* common_string = "a string", common_int = 17, common_float = 17.21 *)
    logic [7: 0] wcomm;
    (* common_int = 21 *)
    logic [7: 0] wcomm_vhd;
    (* common_string = "another string", verilog_string = "a SV string", verilog_int = 3, verilog_float = 11.65 *)
    logic [7: 0] wcomm_ver;
    wcomm = A + B;
    wcomm_vhd = A - B;
    wcomm_ver = 8'(A * B);
    XOUT = (wcomm - wcomm_vhd) + wcomm_ver;
  end
endmodule
