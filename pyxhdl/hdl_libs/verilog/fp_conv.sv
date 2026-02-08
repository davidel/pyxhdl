/* verilator lint_off WIDTH */

// FP_CONV
interface fp_conv;
  parameter integer NX = 11;
  parameter integer NM = 23;

  parameter integer ONX = 11;
  parameter integer ONM = 23;

  localparam integer IN = NX + NM + 1;
  localparam integer IXOFF = fp::EXP_OFFSET(NX);

  localparam integer ON = ONX + ONM + 1;
  localparam integer OXOFF = fp::EXP_OFFSET(ONX);

  localparam integer ZFILL = fp::MAX(ONM - NM, 0);
  localparam integer MSIZE = fp::MIN(ONM, NM);

  function automatic logic [ON - 1: 0] convert;
    input logic [IN - 1: 0] v;

    `IEEE754(NX, NM) pv = v;

    logic [ONM - 1: 0] m;
    logic [ONX - 1: 0] x;
    begin
      // NOTE: Verilator complains when ZFILL is zero ...
      m = {pv.mant[$left(pv.mant) -: MSIZE], (ZFILL + 1)'(0)} >> 1;
      x = OXOFF - IXOFF + pv.exp;

      convert = {pv.sign, x, m};
    end
  endfunction
endinterface

