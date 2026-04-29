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
  function bits_select(value : in std_logic_vector; n : in natural) return std_logic;

  function cvt_unsigned(value : in std_logic; nbits : in natural) return unsigned;
  function cvt_signed(value : in std_logic; nbits : in natural) return signed;

  function cvt_unsigned(value : in std_logic_vector; nbits : in natural) return unsigned;
  function cvt_signed(value : in std_logic_vector; nbits : in natural) return signed;

  function cvt_bits(value : in unsigned) return std_logic_vector;

  function bit_shl(value : in unsigned; nbits : in natural) return unsigned;
  function bit_shr(value : in unsigned; nbits : in natural) return unsigned;

  function bit_shl(value : in std_logic_vector; nbits : in natural) return std_logic_vector;
  function bit_shr(value : in std_logic_vector; nbits : in natural) return std_logic_vector;

  function float_equal(value : in float; ref_value : in real; eps: in real) return boolean;
  function float_equal(value : in real; ref_value : in real; eps: in real) return boolean;
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

  function bits_select(value : in std_logic_vector; n : in natural) return std_logic is
  begin
    return value(n);
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

  function cvt_bits(value : in unsigned) return std_logic_vector is
  begin
    -- This API exists because std_logic_vector(value)(0) is illegal, while
    -- cvt_bits(value)(0) is. Go figure.
    return std_logic_vector(value);
  end function;

  function bit_shl(value : in unsigned; nbits : in natural) return unsigned is
  begin
    return shift_left(value, nbits);
  end function;

  function bit_shr(value : in unsigned; nbits : in natural) return unsigned is
  begin
    return shift_right(value, nbits);
  end function;

  function bit_shl(value : in std_logic_vector; nbits : in natural) return std_logic_vector is
  begin
    return std_logic_vector(shift_left(unsigned(value), nbits));
  end function;

  function bit_shr(value : in std_logic_vector; nbits : in natural) return std_logic_vector is
  begin
    return std_logic_vector(shift_right(unsigned(value), nbits));
  end function;

  function float_equal(value : in float; ref_value : in real; eps: in real) return boolean is
    variable xvalue : real := to_real(value);
    variable toll : real := realmax(abs(xvalue), abs(ref_value)) * eps;
  begin
    return abs(xvalue - ref_value) <= toll;
  end function;

  function float_equal(value : in real; ref_value : in real; eps: in real) return boolean is
    variable toll : real := realmax(abs(value), abs(ref_value)) * eps;
  begin
    return abs(value - ref_value) <= toll;
  end function;
end package body;


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;
use ieee.float_pkg.all;
use std.textio.all;

library work;
use work.all;

-- Entity "GatherTest" is "GatherTest" with:
-- 	args={'A': 'bits(32)', 'XOUT': 'bits(32)'}
-- 	kwargs={}
entity GatherTest is
  port (
    A : in std_logic_vector(31 downto 0);
    XOUT : out std_logic_vector(31 downto 0)
  );
end entity;
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;
use ieee.float_pkg.all;
use std.textio.all;

library work;
use work.all;

-- Entity "GatherTest" is "GatherTest" with:
-- 	args={'A': 'bits(32)', 'XOUT': 'bits(32)'}
-- 	kwargs={}
architecture behavior of GatherTest is
begin
  run : process (A)
    variable XU_gather0 : std_logic_vector(15 downto 0);
    variable XU_gather1 : std_logic_vector(15 downto 0);
  begin
    XU_gather0(0) := A(0);
    XU_gather0(1) := A(2);
    XU_gather0(2) := A(4);
    XU_gather0(3) := A(6);
    XU_gather0(4) := A(8);
    XU_gather0(5) := A(10);
    XU_gather0(6) := A(12);
    XU_gather0(7) := A(14);
    XU_gather0(8) := A(16);
    XU_gather0(9) := A(18);
    XU_gather0(10) := A(20);
    XU_gather0(11) := A(22);
    XU_gather0(12) := A(24);
    XU_gather0(13) := A(26);
    XU_gather0(14) := A(28);
    XU_gather0(15) := A(30);
    XU_gather1(0) := A(1);
    XU_gather1(1) := A(3);
    XU_gather1(2) := A(5);
    XU_gather1(3) := A(7);
    XU_gather1(4) := A(9);
    XU_gather1(5) := A(11);
    XU_gather1(6) := A(13);
    XU_gather1(7) := A(15);
    XU_gather1(8) := A(17);
    XU_gather1(9) := A(19);
    XU_gather1(10) := A(21);
    XU_gather1(11) := A(23);
    XU_gather1(12) := A(25);
    XU_gather1(13) := A(27);
    XU_gather1(14) := A(29);
    XU_gather1(15) := A(31);
    XOUT <= XU_gather0 & XU_gather1;
  end process;
end architecture;
