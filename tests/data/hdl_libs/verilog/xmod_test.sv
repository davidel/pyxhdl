module xmod_test(A, B, C, XOUT);
  input logic [7: 0] A;
  input logic [7: 0] B;
  input logic [7: 0] C;
  output logic [3: 0] XOUT;

  always @(A or B or C)
  run : begin
    XOUT = A + B - C;
  end
endmodule
