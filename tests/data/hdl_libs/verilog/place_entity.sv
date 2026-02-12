module ExEntity(IN_A, IN_B, OUT_DATA);
  parameter integer NBITS = 8;
  parameter integer DELTA = 16;

  input logic [NBITS - 1: 0] IN_A;
  input logic [NBITS - 1: 0] IN_B;
  output logic [NBITS - 1: 0] OUT_DATA;

  assign OUT_DATA = IN_A + IN_B - DELTA;
endmodule
