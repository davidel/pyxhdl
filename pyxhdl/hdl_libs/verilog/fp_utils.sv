/* verilator lint_off WIDTH */

// FP_UTILS
interface fp_utils;
  parameter integer NX = 8;
  parameter integer NM = 23;
  localparam integer CMP_NULP = 2**((NM + 5) / 6);
  localparam integer N = NX + NM + 1;

  localparam integer EXP_MAX = (1 << NX) - 1;
  localparam integer XOFF = fp::EXP_OFFSET(NX);
  localparam integer X64_OFF = fp::EXP_OFFSET(11);
  localparam integer EXP64_MAX = (1 << 11) - 1;

  function automatic logic [N - 1: 0] from_real;
    input real       v;

    localparam integer MSIZE = fp::MAX(NM - 52, 1);

    logic            sign;
    logic [10: 0]    i64x;
    logic [51: 0]    i64m;

    logic signed [11: 0] si64x;

    logic signed [NX - 1: 0] rx;
    logic [NM - 1: 0]        rm;
    begin
      {sign, i64x, i64m} = $realtobits(v);
      si64x = {1'b0, i64x};
      rx = si64x - X64_OFF;
      rx = rx + XOFF;

      if (NM > $bits(i64m)) begin
        rm = {MSIZE'(0), i64m};
      end else begin
        rm = i64m[$left(i64m) -: NM];
        if (i64m[$left(i64m)] == 1) begin
          rm = rm + 1;
        end
      end

      from_real = {sign, rx, rm};
    end
  endfunction

  function automatic real to_real;
    input logic [N - 1: 0] v;

    localparam integer     MSIZE = fp::MIN(52, NM);
    localparam integer     ZFILL = fp::MAX(52 - NM, 0);

    `IEEE754(NX, NM) pv = v;

    logic signed [10: 0]   xd;
    logic [51: 0]          md;

    begin
      if (pv.exp == EXP_MAX) begin
        xd = EXP64_MAX;
      end else begin
        xd = pv.exp - XOFF + X64_OFF;
      end
      // NOTE: Verilator complains when ZFILL is zero ...
      md = {pv.mant[$left(pv.mant) -: MSIZE], (ZFILL + 1)'(0)} >> 1;

      to_real = $bitstoreal({pv.sign, xd, md});
    end
  endfunction

  function automatic real rand_real;
    inout integer seed;

    begin
      rand_real = $itor($random(seed)) / $pow(2.0, 31);
    end
  endfunction

  function automatic integer icloseto;
    input logic [N - 1: 0] v1;
    input logic [N - 1: 0] v2;

    `IEEE754(NX, NM) pv1 = v1;
    `IEEE754(NX, NM) pv2 = v2;

    logic [N - 1: 0]       d = $signed(pv1.mant) - $signed(pv2.mant);
    begin
      icloseto = (CMP_NULP >= fp::ABS(d)) && (pv1.exp == pv2.exp) && (pv1.sign == pv2.sign);
    end
  endfunction

  function automatic logic rcloseto;
    input logic [N - 1: 0] v1;
    input real             v2;
    input real             eps;

    real                   rv1 = to_real(v1);
    real                   delta = fp::FABS(rv1 - v2);
    real                   toll = fp::MAX(fp::FABS(rv1), fp::FABS(v2)) * eps;
    begin
      rcloseto = (delta <= toll);
    end
  endfunction

  function automatic void show_intreal;
    input string     msg;
    input logic [N - 1: 0] v;

    `IEEE754(NX, NM) pv = v;

    begin
      $display("%s(%b %b %b)", msg, pv.sign, pv.exp, pv.mant);
    end
  endfunction

  function automatic void show_real;
    input string msg;
    input real v;

    `IEEE754(NX, NM) pv = from_real(v);

    begin
      $display("%s%f\t(%b %b %b)", msg, v, pv.sign, pv.exp, pv.mant);
    end
  endfunction
endinterface
