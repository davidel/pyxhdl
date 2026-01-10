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

// Entity "ArrayTestEnt" is "ArrayTestEnt" with:
// 	args={'A': 'uint(2, 2, 16)', 'B': 'uint(2, 2, 16)', 'XOUT': 'uint(16)'}
// 	kwargs={}
module ArrayTestEnt(A, B, XOUT);
  input logic [15: 0] A[2][2];
  input logic [15: 0] B[2][2];
  output logic [15: 0] XOUT;
  const logic [15: 0] ar_const[3][2][4];
  logic [15: 0] XOUT_;
  logic [15: 0] ar_const_[3][2][4] = {{{unsigned'(16'(0)), unsigned'(16'(1)), unsigned'(16'(2)), unsigned'(16'(3))}, {unsigned'(16'(4)), unsigned'(16'(5)), unsigned'(16'(6)), unsigned'(16'(7))}}, {{unsigned'(16'(8)), unsigned'(16'(9)), unsigned'(16'(10)), unsigned'(16'(11))}, {unsigned'(16'(12)), unsigned'(16'(13)), unsigned'(16'(14)), unsigned'(16'(15))}}, {{unsigned'(16'(16)), unsigned'(16'(17)), unsigned'(16'(18)), unsigned'(16'(19))}, {unsigned'(16'(20)), unsigned'(16'(21)), unsigned'(16'(22)), unsigned'(16'(23))}}};
  always @(A or B)
  slicing : begin
    XOUT_ = 16'(A[1][0][7: 4] + B[0][1][3: 0]);
  end
  always @(A or B)
  assign_slicing : begin
    XOUT_[3: 0] = A[1][0][7: 4];
    XOUT_[7: 4] = B[0][1][3: 0];
  end
  always @(A or B)
  indexing : begin
    XOUT_ = B[0][int'(A[0][1])];
  end
  always @(A or B)
  np_init : begin
    static logic [15: 0] ar[3][2][4] = {{{unsigned'(16'(0)), unsigned'(16'(1)), unsigned'(16'(2)), unsigned'(16'(3))}, {unsigned'(16'(4)), unsigned'(16'(5)), unsigned'(16'(6)), unsigned'(16'(7))}}, {{unsigned'(16'(8)), unsigned'(16'(9)), unsigned'(16'(10)), unsigned'(16'(11))}, {unsigned'(16'(12)), unsigned'(16'(13)), unsigned'(16'(14)), unsigned'(16'(15))}}, {{unsigned'(16'(16)), unsigned'(16'(17)), unsigned'(16'(18)), unsigned'(16'(19))}, {unsigned'(16'(20)), unsigned'(16'(21)), unsigned'(16'(22)), unsigned'(16'(23))}}};
    XOUT_ = (B[0][1] - ar[1][0][1]) + ar_const[2][1][2];
  end
  assign XOUT = XOUT_;
  assign ar_const = ar_const_;
endmodule
