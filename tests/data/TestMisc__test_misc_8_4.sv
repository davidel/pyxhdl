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



// Entity "Misc" is "Misc" with:
// 	args={'A': 'uint(8)', 'B': 'uint(4)', 'C': 'bits(8)', 'XOUT1': 'uint(8)', 'XOUT2': 'uint(8)'}
// 	kwargs={}
module Misc(A, B, C, XOUT1, XOUT2);
  input logic [7: 0] A;
  input logic [3: 0] B;
  input logic [7: 0] C;
  inout logic [7: 0] XOUT1;
  inout logic [7: 0] XOUT2;
  always @(A or B or C)
  run : begin
    automatic logic [7: 0] na;
    automatic logic [7: 0] nb;
    automatic logic [7: 0] br;
    automatic logic [7: 0] branchy0;
    automatic logic [7: 0] branchy1;
    automatic logic [7: 0] branchy_tuple0;
    automatic logic [7: 0] branchy_tuple1;
    automatic logic [7: 0] branchy_tuple2;
    automatic logic [7: 0] branchy_tuple3;
    automatic logic [7: 0] zz;
    automatic logic [7: 0] branchy_dict0;
    automatic logic [7: 0] branchy_dict1;
    automatic logic [7: 0] rbits = 8'b1101x0x0;
    automatic logic [7: 0] tw1;
    automatic logic [7: 0] tw2;
    automatic logic [7: 0] twd1;
    automatic logic [7: 0] twd2;
    automatic logic [3: 0] twdecl;
    automatic logic [3: 0] twdecl1;
    nb = A + 8'(B);
    na = A - 8'(B);
    if (na[2] == 1'bx) begin
      na = na + nb;
    end else if (na[2] == 1'bx) begin
      na = na - nb;
    end
    if (A > 8'(B)) begin
      branchy0 = A + 8'(B);
    end else begin
      branchy0 = A - 8'(B);
    end
    br = branchy0;
    if (A > 8'(B)) begin
      branchy1 = A + 8'(B);
    end else begin
      branchy1 = A - 8'(B);
    end
    if (A > 8'(B)) begin
      branchy_tuple0 = A + 8'(B);
      branchy_tuple1 = A;
    end else begin
      branchy_tuple0 = A - 8'(B);
      branchy_tuple1 = A + 8'(B);
    end
    if (A > 8'(B)) begin
      branchy_tuple2 = A + 8'(B);
      branchy_tuple3 = A;
    end else begin
      branchy_tuple2 = A - 8'(B);
      branchy_tuple3 = A + 8'(B);
    end
    if (branchy_tuple0 > branchy_tuple1) begin
      branchy_dict0 = branchy_tuple0 + branchy_tuple1;
      branchy_dict1 = branchy_tuple0;
    end else begin
      branchy_dict0 = branchy_tuple0 - branchy_tuple1;
      branchy_dict1 = branchy_tuple0 + branchy_tuple1;
    end
    zz = 8'(branchy_dict0 * branchy_dict1);
    if (C == 8'b0110x110) begin
    end
    if (C != rbits) begin
    end
    if (A == 8'(127)) begin
      zz = 8'(A * 8'(B));
    end
    tw1 = (A - 8'(B)) + (A + 8'(B));
    tw2 = (A - 8'(B)) + (A + 8'(B));
    twdecl = 4'(A + 8'(B));
    twd1 = (A - 8'(B)) + 8'(twdecl);
    twdecl1 = 4'(A + 8'(B));
    twd2 = (A - 8'(B)) + 8'(twdecl1);
    XOUT1 = ((A - 8'(B)) - ((8'(na * nb) - 1) - (na + 8'(nb * 3)))) + zz;
  end
  always @(A or B or C)
  use_self : begin
    XOUT2 = ((A - 8'(B)) + C) + 5;
  end
endmodule
