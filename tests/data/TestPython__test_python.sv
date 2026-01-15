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

// Entity "PythonEnt" is "PythonEnt" with:
// 	args={'DUMMY_A': 'uint(8)', 'DUMMY_OUT': 'uint(8)'}
// 	kwargs={i=17, j=21, f=3.140e+00, s="ABC", l=[1, 2, 3], d={a=3, b=11, c=65}}
module PythonEnt(DUMMY_A, DUMMY_OUT);
  input logic [7: 0] DUMMY_A;
  output logic [7: 0] DUMMY_OUT;
  // i = 17
  // j = 21
  // f = 3.14
  // s = ABC
  // l = [1, 2, 3]
  // d = {'a': 3, 'b': 11, 'c': 65}
  // dd = {22: '23', 23: '24', 24: '25', 25: '26', 26: '27'}
  // ll = ['-3', '-2', '-1', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14']
  // fd = {0: 'ABC 0', 1: 'ABC 1', 2: 'ABC 2', 3: 'ABC 3', 4: 'ABC 4', 5: 'ABC 5', 6: 'ABC 6', 7: 'ABC 7', 8: 'ABC 8', 9: 'ABC 9', 10: 'ABC 10', 11: 'ABC 11'}
  // bigs = AB AB AB AB AB AB AB 
  // a = (4,)
  // [17 18 19 20]
  // ra = (4, 4)
  // [[ 0  1  2  3]
  //  [ 4  5  6  7]
  //  [ 8  9 10 11]
  //  [12 13 14 15]]
  // ras = (4,)
  // [4 5 6 7]
  // rax = (2, 2)
  // [[1 2]
  //  [5 6]]
  // npr = (3,)
  // [5.06 7.48 9.9 ]
  // lres = 21
  // tll = ('-3', '-2', '-1', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14')
  // sinf = 0.0016
  // xlog = 3.1400
  // except = CatchMe {'a': 3, 'b': 11, 'c': 65}
  // else pp = 1120.980
  // finally fd = {0: 'ABC 0', 1: 'ABC 1', 2: 'ABC 2', 3: 'ABC 3', 4: 'ABC 4', 5: 'ABC 5', 6: 'ABC 6', 7: 'ABC 7', 8: 'ABC 8', 9: 'ABC 9', 10: 'ABC 10', 11: 'ABC 11'}
  // gvar = True, -0.5532
  // na = (2,)
  // [ True  True]
  // xss = [1, 2, 'XYZ']
  // xdd = {1: 101, 'A': -1.2, 3.11: True}
  // fctx = 21
  // nret = None
  // yield_fn = 4
  // yield_fn = 5
  // yield_fn = 6
  // yield_from_fn = 17
  // yield_from_fn = 21
  // yield_from_fn = 33
  // cargs = (1, 3.14, 'XYZ')
endmodule
