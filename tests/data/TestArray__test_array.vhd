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

-- Entity "ArrayTestEnt" is "ArrayTestEnt" with:
-- 	args={'A': 'uint(2, 2, 16)', 'B': 'uint(2, 2, 16)', 'XOUT': 'uint(16)'}
-- 	kwargs={}
entity ArrayTestEnt is
  port (
    A : in pyxhdl.uint_array2d(0 to 1)(0 to 1)(15 downto 0);
    B : in pyxhdl.uint_array2d(0 to 1)(0 to 1)(15 downto 0);
    XOUT : out unsigned(15 downto 0)
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

-- Entity "ArrayTestEnt" is "ArrayTestEnt" with:
-- 	args={'A': 'uint(2, 2, 16)', 'B': 'uint(2, 2, 16)', 'XOUT': 'uint(16)'}
-- 	kwargs={}
architecture behavior of ArrayTestEnt is
  signal ar : pyxhdl.uint_array3d(0 to 2)(0 to 1)(0 to 3)(15 downto 0) := (((to_unsigned(0, 16), to_unsigned(1, 16), to_unsigned(2, 16), to_unsigned(3, 16)), (to_unsigned(4, 16), to_unsigned(5, 16), to_unsigned(6, 16), to_unsigned(7, 16))), ((to_unsigned(8, 16), to_unsigned(9, 16), to_unsigned(10, 16), to_unsigned(11, 16)), (to_unsigned(12, 16), to_unsigned(13, 16), to_unsigned(14, 16), to_unsigned(15, 16))), ((to_unsigned(16, 16), to_unsigned(17, 16), to_unsigned(18, 16), to_unsigned(19, 16)), (to_unsigned(20, 16), to_unsigned(21, 16), to_unsigned(22, 16), to_unsigned(23, 16))));
  constant ar_const : pyxhdl.uint_array3d(0 to 2)(0 to 1)(0 to 3)(15 downto 0) := (((to_unsigned(0, 16), to_unsigned(1, 16), to_unsigned(2, 16), to_unsigned(3, 16)), (to_unsigned(4, 16), to_unsigned(5, 16), to_unsigned(6, 16), to_unsigned(7, 16))), ((to_unsigned(8, 16), to_unsigned(9, 16), to_unsigned(10, 16), to_unsigned(11, 16)), (to_unsigned(12, 16), to_unsigned(13, 16), to_unsigned(14, 16), to_unsigned(15, 16))), ((to_unsigned(16, 16), to_unsigned(17, 16), to_unsigned(18, 16), to_unsigned(19, 16)), (to_unsigned(20, 16), to_unsigned(21, 16), to_unsigned(22, 16), to_unsigned(23, 16))));
begin
  slicing : process (A, B)
  begin
    XOUT <= resize(A(1)(0)(7 downto 4) + B(0)(1)(3 downto 0), 16);
  end process;
  assign_slicing : process (A, B)
  begin
    XOUT(3 downto 0) <= A(1)(0)(7 downto 4);
    XOUT(7 downto 4) <= B(0)(1)(3 downto 0);
  end process;
  indexing : process (A, B)
  begin
    XOUT <= B(0)(to_integer(A(0)(1)));
  end process;
  np_init : process (A, B)
  begin
    XOUT <= (B(0)(1) - ar(1)(0)(1)) + ar_const(2)(1)(2);
  end process;
end architecture;
