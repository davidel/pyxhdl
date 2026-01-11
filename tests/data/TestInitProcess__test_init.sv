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

// Entity "InitProcess" is "InitProcess" with:
// 	args={'A': 'uint(8)', 'B': 'uint(8)', 'XOUT': 'uint(8)'}
// 	kwargs={init=[[ 0  1  2  3]
//  [ 4  5  6  7]
//  [ 8  9 10 11]
//  [12 13 14 15]]}
module InitProcess(A, B, XOUT);
  input logic [7: 0] A;
  input logic [7: 0] B;
  output logic [7: 0] XOUT;
  logic [7: 0] arr[4][4];
  logic [7: 0] zarr[4][4] = '{4{'{4{unsigned'(8'(1))}}}};
  logic [7: 0] temp = unsigned'(8'(21));
  initial
  init : begin
    arr[0][0] = unsigned'(8'(0));
    arr[0][1] = unsigned'(8'(1));
    arr[0][2] = unsigned'(8'(2));
    arr[0][3] = unsigned'(8'(3));
    arr[1][0] = unsigned'(8'(4));
    arr[1][1] = unsigned'(8'(5));
    arr[1][2] = unsigned'(8'(6));
    arr[1][3] = unsigned'(8'(7));
    arr[2][0] = unsigned'(8'(8));
    arr[2][1] = unsigned'(8'(9));
    arr[2][2] = unsigned'(8'(10));
    arr[2][3] = unsigned'(8'(11));
    arr[3][0] = unsigned'(8'(12));
    arr[3][1] = unsigned'(8'(13));
    arr[3][2] = unsigned'(8'(14));
    arr[3][3] = unsigned'(8'(15));
  end
  always @(A or B)
  run : begin
    XOUT = ((A - 8'(3 * B)) - 8'(temp * arr[1][2])) + 8'(11 * zarr[2][3]);
  end
endmodule
