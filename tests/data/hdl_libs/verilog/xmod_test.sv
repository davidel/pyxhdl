module xmod_test(A, B, XOUT);
  input logic [7: 0] A;
  input logic [7: 0] B;
  output logic [3: 0] XOUT;

  always @(A or B)
  run : begin
    XOUT = A + B;
  end
endmodule
