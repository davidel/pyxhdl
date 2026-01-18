/* verilator lint_off WIDTH */

// FP_CONV
interface fp_conv;
  parameter integer INX = 11;
  parameter integer INM = 23;

  parameter integer ONX = 11;
  parameter integer ONM = 23;

  localparam integer IN = INX + INM + 1;
  localparam integer IXOFF = fp::EXP_OFFSET(INX);

  localparam integer ON = ONX + ONM + 1;
  localparam integer OXOFF = fp::EXP_OFFSET(ONX);

  localparam integer ZFILL = (ONM > INM) ? ONM - INM : 0;
  localparam integer MSIZE = fp::MIN(ONM, INM);

  function automatic logic [ON - 1: 0] convert;
    input logic [IN - 1: 0] v;

    `IEEE754(INX, INM) pv = v;

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

