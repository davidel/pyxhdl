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



// Entity "StateMachine" is "StateMachine" with:
// 	args={'CLK': 'bits(1)', 'RST_N': 'bits(1)', 'BITLINE': 'bits(1)', 'RDEN': 'bits(1)', 'RDATA': 'uint(8)'}
// 	kwargs={}
module StateMachine(CLK, RST_N, BITLINE, RDEN, RDATA);
  input logic CLK;
  input logic RST_N;
  input logic BITLINE;
  output logic RDEN;
  output logic [7: 0] RDATA;
  logic [2: 0] state = 3'(0);
  logic [3: 0] count = 4'(0);
  logic [7: 0] value;
  always_ff @(posedge CLK)
  state_machine : begin
    if (&(!RST_N)) begin
      state <= 3'(0);
      count <= 4'(0);
      RDEN <= 1'(0);
      RDATA <= 8'(1'bx);
    end else begin
      case (state)
        3'(0): begin
          if (BITLINE == 1'(1)) begin
            state <= 3'(1);
          end
        end
        3'(1): begin
          if (BITLINE == 1'(0)) begin
            state <= 3'(2);
            count <= 4'(0);
            value <= 8'(0);
            RDEN <= 1'(0);
          end
        end
        3'(2): begin
          value <= (value << 1) | 8'(BITLINE);
          if (count == 4'(7)) begin
            state <= 3'(4);
          end else begin
            count <= count + 1;
          end
        end
        3'(4): begin
          if (BITLINE == 1'(0)) begin
            RDEN <= 1'(1);
            RDATA <= value;
          end
          state <= 3'(0);
        end
        default: begin
        end
      endcase
    end
  end
endmodule
