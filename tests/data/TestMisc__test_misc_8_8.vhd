-- PyXHDL support functions.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;
use ieee.float_pkg.all;

package pyxhdl is
  type uint_array1d is array(natural range <>) of unsigned;
  type uint_array2d is array(natural range <>) of uint_array1d;
  type uint_array3d is array(natural range <>) of uint_array2d;
  type uint_array4d is array(natural range <>) of uint_array3d;

  type sint_array1d is array(natural range <>) of signed;
  type sint_array2d is array(natural range <>) of sint_array1d;
  type sint_array3d is array(natural range <>) of sint_array2d;
  type sint_array4d is array(natural range <>) of sint_array3d;

  type bits_array1d is array(natural range <>) of std_logic_vector;
  type bits_array2d is array(natural range <>) of bits_array1d;
  type bits_array3d is array(natural range <>) of bits_array2d;
  type bits_array4d is array(natural range <>) of bits_array3d;

  type slv_array1d is array(natural range <>) of std_logic;
  type slv_array2d is array(natural range <>) of slv_array1d;
  type slv_array3d is array(natural range <>) of slv_array2d;
  type slv_array4d is array(natural range <>) of slv_array3d;

  type float_array1d is array(natural range <>) of float;
  type float_array2d is array(natural range <>) of float_array1d;
  type float_array3d is array(natural range <>) of float_array2d;
  type float_array4d is array(natural range <>) of float_array3d;

  type bool_array1d is array(natural range <>) of boolean;
  type bool_array2d is array(natural range <>) of bool_array1d;
  type bool_array3d is array(natural range <>) of bool_array2d;
  type bool_array4d is array(natural range <>) of bool_array3d;

  type integer_array1d is array(natural range <>) of integer;
  type integer_array2d is array(natural range <>) of integer_array1d;
  type integer_array3d is array(natural range <>) of integer_array2d;
  type integer_array4d is array(natural range <>) of integer_array3d;

  type real_array1d is array(natural range <>) of real;
  type real_array2d is array(natural range <>) of real_array1d;
  type real_array3d is array(natural range <>) of real_array2d;
  type real_array4d is array(natural range <>) of real_array3d;

  function sint_ifexp(test : in boolean; texp : in signed; fexp : in signed) return signed;
  function uint_ifexp(test : in boolean; texp : in unsigned; fexp : in unsigned) return unsigned;
  function bool_ifexp(test : in boolean; texp : in boolean; fexp : in boolean) return boolean;
  function float_ifexp(test : in boolean; texp : in float; fexp : in float) return float;
  function bits_ifexp(test : in boolean; texp : in std_logic_vector; fexp : in std_logic_vector) return std_logic_vector;
  function bits_ifexp(test : in boolean; texp : in std_logic; fexp : in std_logic) return std_logic;
  function real_ifexp(test : in boolean; texp : in real; fexp : in real) return real;
  function integer_ifexp(test : in boolean; texp : in integer; fexp : in integer) return integer;

  function bits_resize(value : in std_logic; nbits : in natural) return std_logic_vector;
  function bits_resize(value : in std_logic_vector; nbits : in natural) return std_logic_vector;

  function cvt_unsigned(value : in std_logic; nbits : in natural) return unsigned;
  function cvt_signed(value : in std_logic; nbits : in natural) return signed;

  function cvt_unsigned(value : in std_logic_vector; nbits : in natural) return unsigned;
  function cvt_signed(value : in std_logic_vector; nbits : in natural) return signed;

  function float_equal(value : in float; ref_value : in real; eps: in real) return boolean;
end package;

package body pyxhdl is
  function sint_ifexp(test : in boolean; texp : in signed; fexp : in signed) return signed is
  begin
    if test then
      return texp;
    else
      return fexp;
    end if;
  end function;

  function uint_ifexp(test : in boolean; texp : in unsigned; fexp : in unsigned) return unsigned is
  begin
    if test then
      return texp;
    else
      return fexp;
    end if;
  end function;

  function bool_ifexp(test : in boolean; texp : in boolean; fexp : in boolean) return boolean is
  begin
    if test then
      return texp;
    else
      return fexp;
    end if;
  end function;

  function float_ifexp(test : in boolean; texp : in float; fexp : in float) return float is
  begin
    if test then
      return texp;
    else
      return fexp;
    end if;
  end function;

  function bits_ifexp(test : in boolean; texp : in std_logic_vector; fexp : in std_logic_vector) return std_logic_vector is
  begin
    if test then
      return texp;
    else
      return fexp;
    end if;
  end function;

  function bits_ifexp(test : in boolean; texp : in std_logic; fexp : in std_logic) return std_logic is
  begin
    if test then
      return texp;
    else
      return fexp;
    end if;
  end function;

  function real_ifexp(test : in boolean; texp : in real; fexp : in real) return real is
  begin
    if test then
      return texp;
    else
      return fexp;
    end if;
  end function;

  function integer_ifexp(test : in boolean; texp : in integer; fexp : in integer) return integer is
  begin
    if test then
      return texp;
    else
      return fexp;
    end if;
  end function;

  function bits_resize(value : in std_logic; nbits : in natural) return std_logic_vector is
    variable res : std_logic_vector(nbits - 1 downto 0) := (others => '0');
  begin
    res(0) := value;
    return res;
  end function;

  function bits_resize(value : in std_logic_vector; nbits : in natural) return std_logic_vector is
    variable res : std_logic_vector(nbits - 1 downto 0) := (others => '0');
  begin
    if nbits >= value'length then
      res(value'length - 1 downto 0) := value;
    else
      res := value(nbits - 1 downto 0);
    end if;
    return res;
  end function;

  function cvt_unsigned(value : in std_logic; nbits : in natural) return unsigned is
  begin
    return unsigned(bits_resize(value, nbits));
  end function;

  function cvt_signed(value : in std_logic; nbits : in natural) return signed is
  begin
    return signed(bits_resize(value, nbits));
  end function;

  function cvt_unsigned(value : in std_logic_vector; nbits : in natural) return unsigned is
  begin
    return unsigned(bits_resize(value, nbits));
  end function;

  function cvt_signed(value : in std_logic_vector; nbits : in natural) return signed is
  begin
    return signed(bits_resize(value, nbits));
  end function;

  function float_equal(value : in float; ref_value : in real; eps: in real) return boolean is
    variable xvalue : real := to_real(value);
    variable toll : real := realmax(abs(xvalue), abs(ref_value)) * eps;
  begin
    return abs(xvalue - ref_value) <= toll;
  end function;
end package body;


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;
use ieee.float_pkg.all;

library work;
use work.all;

-- Entity "Misc" is "Misc" with:
-- 	args={'A': 'uint(8)', 'B': 'uint(8)', 'C': 'bits(8)', 'XOUT': 'uint(8)'}
-- 	kwargs={}
entity Misc is
  port (
    A : in unsigned(7 downto 0);
    B : in unsigned(7 downto 0);
    C : in std_logic_vector(7 downto 0);
    XOUT : inout unsigned(7 downto 0)
  );
end entity;
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;
use ieee.float_pkg.all;

library work;
use work.all;

-- Entity "Misc" is "Misc" with:
-- 	args={'A': 'uint(8)', 'B': 'uint(8)', 'C': 'bits(8)', 'XOUT': 'uint(8)'}
-- 	kwargs={}
architecture behavior of Misc is
begin
  run : process (A, B, C)
    variable na : unsigned(7 downto 0);
    variable nb : unsigned(7 downto 0);
    variable br : unsigned(7 downto 0);
    variable branchy_0 : unsigned(7 downto 0);
    variable branchy_1 : unsigned(7 downto 0);
    variable branchy_tuple_0 : unsigned(7 downto 0);
    variable branchy_tuple_1 : unsigned(7 downto 0);
    variable branchy_tuple_2 : unsigned(7 downto 0);
    variable branchy_tuple_3 : unsigned(7 downto 0);
    variable zz : unsigned(7 downto 0);
    variable branchy_dict_0 : unsigned(7 downto 0);
    variable branchy_dict_1 : unsigned(7 downto 0);
    variable rbits : std_logic_vector(7 downto 0) := "1101X0X0";
    variable tw1 : unsigned(7 downto 0);
    variable tw2 : unsigned(7 downto 0);
    variable twd1 : unsigned(7 downto 0);
    variable twd2 : unsigned(7 downto 0);
    variable twdecl : unsigned(7 downto 0);
    variable twdecl_1 : unsigned(7 downto 0);
  begin
    nb := A + B;
    na := A - B;
    if na(2) = 'X' then
      na := na + nb;
    elsif na(2) = 'U' then
      na := na - nb;
    end if;
    if A > B then
      branchy_0 := A + B;
    else
      branchy_0 := A - B;
    end if;
    br := branchy_0;
    if A > B then
      branchy_1 := A + B;
    else
      branchy_1 := A - B;
    end if;
    if A > B then
      branchy_tuple_0 := A + B;
      branchy_tuple_1 := A;
    else
      branchy_tuple_0 := A - B;
      branchy_tuple_1 := A + B;
    end if;
    if A > B then
      branchy_tuple_2 := A + B;
      branchy_tuple_3 := A;
    else
      branchy_tuple_2 := A - B;
      branchy_tuple_3 := A + B;
    end if;
    if branchy_tuple_0 > branchy_tuple_1 then
      branchy_dict_0 := branchy_tuple_0 + branchy_tuple_1;
      branchy_dict_1 := branchy_tuple_0;
    else
      branchy_dict_0 := branchy_tuple_0 - branchy_tuple_1;
      branchy_dict_1 := branchy_tuple_0 + branchy_tuple_1;
    end if;
    zz := resize(branchy_dict_0 * branchy_dict_1, 8);
    if C = "0110X110" then
    end if;
    if C /= rbits then
    end if;
    if A = to_unsigned(127, 8) then
      zz := resize(A * B, 8);
    end if;
    tw1 := (A - B) + (A + B);
    tw2 := (A - B) + (A + B);
    twdecl := A + B;
    twd1 := (A - B) + twdecl;
    twdecl_1 := A + B;
    twd2 := (A - B) + twdecl_1;
    XOUT <= ((A - B) - ((resize(na * nb, 8) - 1) - (na + resize(nb * 3, 8)))) + zz;
  end process;
  use_self : process (A, B, C)
  begin
    XOUT <= ((A - B) + pyxhdl.cvt_unsigned(C, 8)) + 4;
  end process;
end architecture;
