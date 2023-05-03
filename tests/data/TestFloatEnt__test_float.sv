/* verilator lint_off WIDTH */

`timescale 1 ns / 1 ps

`define MAX(A, B) ((A > B) ? A : B)
`define MIN(A, B) ((A > B) ? B : A)
`define ABS(A) (($signed(A) >= 0) ? A : -$signed(A))
`define FABS(A) ((A >= 0.0) ? A : -A)

`define EXP_OFFSET(NX) (2**(NX - 1) - 1)

// This in theory should be a typedef within the FPU interface, but then
// many HDL tools do not support hierarchical type dereferencing.
`define IEEE754(NX, NM) \
struct packed { \
  logic  sign; \
  logic [NX - 1: 0] exp; \
  logic [NM - 1: 0] mant; \
  }


// PyXHDL support functions.

/* verilator lint_off WIDTH */

// FP_CONV
interface fp_conv;
  parameter integer INX = 11;
  parameter integer INM = 23;

  parameter integer ONX = 11;
  parameter integer ONM = 23;

  localparam integer IN = INX + INM + 1;
  localparam integer IXOFF = `EXP_OFFSET(INX);

  localparam integer ON = ONX + ONM + 1;
  localparam integer OXOFF = `EXP_OFFSET(ONX);

  localparam integer ZFILL = (ONM > INM) ? ONM - INM : 0;
  localparam integer MSIZE = `MIN(ONM, INM);

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


/* verilator lint_off WIDTH */

// CLZ
interface clz_mod;
  parameter integer N = 32;
  localparam integer NPAD = ((N + 3) / 4) * 4;
  localparam integer NB = $clog2(N);

  function automatic logic [2: 0] clz4;
    input [3: 0]     vin;

    logic [2: 0]     res;
    begin
      case (vin)
        4'b0000: res = 4;
        4'b0001: res = 3;
        4'b0010: res = 2;
        4'b0011: res = 2;

        4'b0100: res = 1;
        4'b0101: res = 1;
        4'b0110: res = 1;
        4'b0111: res = 1;

        default: res = 0;
      endcase
      clz4 = res;
    end
  endfunction

  function automatic logic [NB - 1: 0] clz;
    input logic [N - 1: 0] vin;

    logic [NPAD - 1: 0]    vpad;
    logic                  zmore = 1;
    logic [2: 0]           cres;
    logic [NB - 1: 0]      res;

    integer                i;
    begin
      vpad = vin;

      res = 0;
      for (i = NPAD - 4; i >= 0; i = i - 4) begin
        cres = clz4(vpad[i +: 4]);
        if (zmore) begin
          res = res + cres;
          zmore = zmore & cres[2];
        end
      end

      clz = res;
    end
  endfunction
endinterface


// FPU
interface fpu;
  parameter integer NX = 11;
  parameter integer NM = 23;
  localparam integer N = NX + NM + 1;
  parameter integer  NINT = N;
  localparam integer XOFF = `EXP_OFFSET(NX);
  localparam integer ADDSUB_PAD = 3;

  clz_mod #(.N (NM)) add_clz();
  clz_mod #(.N (`MAX(NINT, N))) from_integer_clz();

  function automatic logic [N - 1: 0] inf;
    input logic      s;
    begin
      inf = {s, {NX{1'b1}}, {NM{1'b0}}};
    end
  endfunction

  function automatic bit [N - 1: 0] nan;
    begin
      nan = {1'b0, {NX{1'b1}}, {(NM - 1){1'b0}}, 1'b1};
    end
  endfunction

  function automatic bit is_abn;
    input logic [NX - 1: 0] x;

    begin
      is_abn = (&x == 1'b1);
    end
  endfunction

  function automatic bit is_nan;
    input logic [NM - 1: 0] m;

    begin
      is_nan = (|m != 1'b0);
    end
  endfunction

  function automatic bit is_inf;
    input logic [NM - 1: 0] m;

    begin
      is_inf = (|m == 1'b0);
    end
  endfunction

  function automatic bit is_zero;
    input logic [NX - 1: 0] x;

    begin
      is_zero = (|x == 1'b0);
    end
  endfunction

  function automatic bit [N - 1: 0] zero;
    begin
      zero = {N{1'b0}};
    end
  endfunction

  function automatic bit [N - 1: 0] one;
    begin
      one = {1'b0, NX'(XOFF), NM'(0)};
    end
  endfunction

  function automatic logic signed [NINT - 1: 0] to_integer;
    input logic [N - 1: 0] v;

    localparam integer     NR = `MAX(NINT, NM + 1);

    `IEEE754(NX, NM) pv = v;

    logic signed [NR - 1: 0] mr;
    logic signed [NX - 1: 0] sx;
    begin
      mr = {1'b1, pv.mant};
      sx = NM + XOFF - pv.exp;
      if (sx >= 0) begin
        mr = mr >> sx;
      end else begin
        mr = mr << (-sx);
      end
      to_integer = (pv.sign) ? -mr : mr;
    end
  endfunction

  function automatic logic [N - 1: 0] from_integer;
    input logic signed [NINT - 1: 0] v;

    localparam integer               NR = `MAX(NINT, NM + 1);

    logic                            sign;
    logic [from_integer_clz.NB - 1: 0] nclz;
    logic signed [from_integer_clz.NB: 0] sh;
    logic signed [NR - 1: 0]              m;
    logic signed [NX - 1: 0]              x;
    begin
      if (v < 0) begin
        m = -v;
        sign = 1;
      end else begin
        m = v;
        sign = 0;
      end

      nclz = from_integer_clz.clz(m);
      sh = NR - NM - 1 - nclz;
      if (sh >= 0) begin
        m = m >> sh;
      end else begin
        m = m << (-sh);
      end
      x = XOFF + NM + sh;

      from_integer = {sign, x, m[NM - 1: 0]};
    end
  endfunction

  function automatic logic [N - 1: 0] neg;
    input logic [N - 1: 0] v;

    `IEEE754(NX, NM) pv = v;

    begin
      neg = {~pv.sign, pv.exp, pv.mant};
    end
  endfunction

  function automatic logic [N - 1: 0] add;
    input logic [N - 1: 0] v1;
    input logic [N - 1: 0] v2;

    `IEEE754(NX, NM) pv1 = v1;
    `IEEE754(NX, NM) pv2 = v2;

    logic [add_clz.NB - 1: 0] nclz;

    logic                  s;
    logic [NX - 1: 0]      dx, xr;
    logic [NM + 2 + ADDSUB_PAD: 0] m1p, m2p;
    logic [NM + 2 + ADDSUB_PAD: 0] mas;
    logic [NM - 1: 0]              mr;
    begin
      if (is_abn(pv1.exp)) begin
        add = v1;
      end else if (is_abn(pv2.exp)) begin
        add = v2;
      end else begin
        m1p = {3'b001, pv1.mant, {ADDSUB_PAD{1'b0}}};
        m2p = {3'b001, pv2.mant, {ADDSUB_PAD{1'b0}}};

        if (pv1.exp > pv2.exp) begin
          dx = pv1.exp - pv2.exp;
          xr = pv1.exp;
          m2p = m2p >> dx;
          if (pv1.sign == pv2.sign) begin
            mas = m1p + m2p;
          end else begin
            mas = m1p - m2p;
          end
          s = pv1.sign;
        end else begin
          dx = pv2.exp - pv1.exp;
          xr = pv2.exp;
          m1p = m1p >> dx;
          if (pv1.sign == pv2.sign) begin
            mas = m1p + m2p;
            s = pv1.sign;
          end else begin
            mas = m1p - m2p;
            s = pv1.sign ^ mas[$left(mas)];
          end
        end

        if (mas[$left(mas)] == 1) begin
          mas = -$signed(mas);
        end

        nclz = add_clz.clz(mas[$left(mas) -: NM]);

        mas = mas << nclz;
        mr = mas[$left(mas) - 1 -: $bits(mr)];
        xr = xr - nclz + ($bits(mas) - NM - ADDSUB_PAD - 1);

        add = {s, xr, mr};
      end
    end
  endfunction

  function automatic logic [N - 1: 0] sub;
    input logic [N - 1: 0] v1;
    input logic [N - 1: 0] v2;

    `IEEE754(NX, NM) pv2 = v2;
    begin
      pv2.sign = ~pv2.sign;

      sub = add(v1, pv2);
    end
  endfunction

  function automatic logic [N - 1: 0] mul;
    input logic [N - 1: 0] v1;
    input logic [N - 1: 0] v2;

    `IEEE754(NX, NM) pv1 = v1;
    `IEEE754(NX, NM) pv2 = v2;

    logic                  s;
    logic [NX: 0]          xr;
    logic [2 * NM + 2 - 1: 0] m1p, m2p, mmul;
    logic [NM - 1: 0]         mr;
    begin
      if (is_abn(pv1.exp) || is_zero(pv1.exp)) begin
        mul = v1;
      end else if (is_abn(pv2.exp) || is_zero(pv2.exp)) begin
        mul = v2;
      end else begin
        m1p = {1'b1, pv1.mant};
        m2p = {1'b1, pv2.mant};

        s = pv1.sign ^ pv2.sign;
        xr = {1'b0, pv1.exp} + {1'b0, pv2.exp} - XOFF;

        mmul = m1p * m2p;
        if (mmul[$left(mmul)] == 1) begin
          xr = xr + 1;
          mr = mmul >> (NM + 1);
        end else begin
          mr = mmul >> NM;
        end

        mul = {s, xr[$left(xr) - 1: 0], mr};
      end
    end
  endfunction

  function automatic logic [N - 1: 0] div;
    input logic [N - 1: 0] v1;
    input logic [N - 1: 0] v2;

    `IEEE754(NX, NM) pv1 = v1;
    `IEEE754(NX, NM) pv2 = v2;

    logic                  s;
    logic [NX: 0]          xr;
    logic [2 * NM + 2 - 1: 0] m1p, mdiv;
    logic [NM: 0]             m2p;
    logic [NM - 1: 0]         mr;
    begin
      if (is_abn(pv1.exp)) begin
        div = v1;
      end else if (is_zero(pv1.exp)) begin
        div = is_zero(pv2.exp) || is_abn(pv2.exp) ? nan() : v1;
      end else if (is_abn(pv2.exp)) begin
        div = v2;
      end else if (is_zero(pv2.exp)) begin
        div = inf(pv1.sign ^ pv2.sign);
      end else begin
        m1p = {1'b1, pv1.mant, {(NM + 1){1'b0}}};
        m2p = {1'b1, pv2.mant};

        s = pv1.sign ^ pv2.sign;
        xr = {1'b0, pv1.exp} + XOFF - {1'b0, pv2.exp};

        mdiv = m1p / m2p;
        if (mdiv[$left(mdiv) - NM] == 1) begin
          mr = mdiv >> 1;
        end else begin
          xr = xr - 1;
          mr = mdiv;
        end

        div = {s, xr[$left(xr) - 1: 0], mr};
      end
    end
  endfunction
endinterface


// Entity "FloatEnt" is "FloatEnt" with:
// 	args={'A': 'float(32)', 'B': 'float(32)', 'XOUT': 'float(16)'}
// 	kwargs={}
module FloatEnt(A, B, XOUT);
  input logic [31: 0] A;
  input logic [31: 0] B;
  output logic [15: 0] XOUT;
  logic [15: 0] XOUT_;
  fpu #(.NX(8), .NM(23)) fpu_1();
  fp_conv #(.INX(8), .INM(23), .ONX(5), .ONM(10)) fp_conv_1();
  always @(A or B)
  run : begin
    logic [31: 0] add;
    logic [31: 0] mul;
    logic [31: 0] div;
    logic [31: 0] sub;
    add = fpu_1.add(A, B);
    mul = fpu_1.mul(A, B);
    div = fpu_1.div(A, B);
    sub = fpu_1.sub(A, B);
    XOUT_ = fp_conv_1.convert(fpu_1.add(fpu_1.sub(fpu_1.add(add, mul), div), fpu_1.mul(sub, fpu_1.sub(fpu_1.add(A, 32'b01000000110000000000000000000000), fpu_1.add(A, 32'b01000000110001111010111000010100)))));
  end
  assign XOUT = XOUT_;
endmodule
