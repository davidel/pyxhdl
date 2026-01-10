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

// Entity "Misc" is "Misc" with:
// 	args={'A': 'uint(8)', 'B': 'uint(8)', 'C': 'bits(8)', 'XOUT1': 'uint(8)', 'XOUT2': 'uint(8)'}
// 	kwargs={}
module Misc(A, B, C, XOUT1, XOUT2);
  input logic [7: 0] A;
  input logic [7: 0] B;
  input logic [7: 0] C;
  inout logic [7: 0] XOUT1;
  inout logic [7: 0] XOUT2;
  logic [7: 0] XOUT1_;
  logic [7: 0] XOUT2_;
  always @(A or B or C)
  run : begin
    logic [7: 0] na;
    logic [7: 0] nb;
    logic [7: 0] br;
    logic [7: 0] branchy_0;
    logic [7: 0] branchy_1;
    logic [7: 0] branchy_tuple_0;
    logic [7: 0] branchy_tuple_1;
    logic [7: 0] branchy_tuple_2;
    logic [7: 0] branchy_tuple_3;
    logic [7: 0] zz;
    logic [7: 0] branchy_dict_0;
    logic [7: 0] branchy_dict_1;
    logic [7: 0] rbits = 8'b1101x0x0;
    logic [7: 0] tw1;
    logic [7: 0] tw2;
    logic [7: 0] twd1;
    logic [7: 0] twd2;
    logic [7: 0] twdecl;
    logic [7: 0] twdecl_1;
    nb = A + B;
    na = A - B;
    if (na[2] == 1'bx) begin
      na = na + nb;
    end else if (na[2] == 1'bx) begin
      na = na - nb;
    end
    if (A > B) begin
      branchy_0 = A + B;
    end else begin
      branchy_0 = A - B;
    end
    br = branchy_0;
    if (A > B) begin
      branchy_1 = A + B;
    end else begin
      branchy_1 = A - B;
    end
    if (A > B) begin
      branchy_tuple_0 = A + B;
      branchy_tuple_1 = A;
    end else begin
      branchy_tuple_0 = A - B;
      branchy_tuple_1 = A + B;
    end
    if (A > B) begin
      branchy_tuple_2 = A + B;
      branchy_tuple_3 = A;
    end else begin
      branchy_tuple_2 = A - B;
      branchy_tuple_3 = A + B;
    end
    if (branchy_tuple_0 > branchy_tuple_1) begin
      branchy_dict_0 = branchy_tuple_0 + branchy_tuple_1;
      branchy_dict_1 = branchy_tuple_0;
    end else begin
      branchy_dict_0 = branchy_tuple_0 - branchy_tuple_1;
      branchy_dict_1 = branchy_tuple_0 + branchy_tuple_1;
    end
    zz = 8'(branchy_dict_0 * branchy_dict_1);
    if (C == 8'b0110x110) begin
    end
    if (C != rbits) begin
    end
    if (A == 8'(127)) begin
      zz = 8'(A * B);
    end
    tw1 = (A - B) + (A + B);
    tw2 = (A - B) + (A + B);
    twdecl = A + B;
    twd1 = (A - B) + twdecl;
    twdecl_1 = A + B;
    twd2 = (A - B) + twdecl_1;
    XOUT1_ = ((A - B) - ((8'(na * nb) - 1) - (na + 8'(nb * 3)))) + zz;
  end
  always @(A or B or C)
  use_self : begin
    XOUT2_ = ((A - B) + C) + 5;
  end
  assign XOUT1 = XOUT1_;
  assign XOUT2 = XOUT2_;
endmodule
