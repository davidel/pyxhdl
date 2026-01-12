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


package dummy;
  function automatic logic [7: 0] func;
    input logic [7: 0] a, b;
    begin
      func = a + b;
    end
  endfunction

  task proc;
    input logic [7: 0] a, b;
    begin
      assert (a > b) else $error("Compare failed!");
    end
  endtask
endpackage

// Entity "XLib" is "XLib" with:
// 	args={'CLK': 'bits(1)', 'A': 'uint(8)', 'B': 'uint(8)', 'XOUT': 'uint(8)'}
// 	kwargs={arg1=17, arg2="PyXHDL"}
module XLib(CLK, A, B, XOUT);
  input logic CLK;
  input logic [7: 0] A;
  input logic [7: 0] B;
  output logic [7: 0] XOUT;
  logic [7: 0] e;
  logic [7: 0] ctx;
  logic [7: 0] z;
  logic [7: 0] assigned;
  always @(CLK or A or B)
  run : begin
    $display("%s%s%s%s%s%s%s%s%s%s%s", "TIME=", $sformatf("%t", $time), " A=", $sformatf("%d", A - B), " B=", $sformatf("%d", A + B), " arg1=", "17", " arg2=", "PyXHDL", " $$vanilla");
    $display("%s%s%s%s%s%s%s%s%s%s%s", "TIME=", $sformatf("%t", $time), " A=", $sformatf("%d", A), " B=", $sformatf("%d", B), " arg1=", "17", " arg2=", "PyXHDL", " $$vanilla");
    dummy::proc((A + B) + B, A - 8'((A + B) * 2));
    e = dummy::func(A + 1, 8'(B * 3));
    #10 ctx = 8'(A * B);
    z = ((A + B) - A) + B;
    z = 8'(A * B);
    assigned = z - B;
  end
  always @(*)
  waiter : begin
    @((A == unsigned'(8'(1))));
  end
endmodule
