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

-- Entity "NestedInterfaceTest" is "NestedInterfaceTest" with:
-- 	args={'CLK': 'bits(1)', 'X': 'uint(8)', 'Y': 'uint(8)', 'Q': 'uint(8)'}
-- 	kwargs={}
entity NestedInterfaceTest is
  port (
    CLK : in std_logic;
    X : in unsigned(7 downto 0);
    Y : out unsigned(7 downto 0);
    Q : out unsigned(7 downto 0)
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

-- Entity "NestedIfc" is "NestedIfc" with:
-- 	args={'CLK': 'bits(1)', 'OIFC': 'InterfaceView(an_int:17, CLK:bits(1), IIFCA:InterfaceView(CLK:bits(1), X:uint(8), Y:uint(8), Z:uint(8)), IIFCB:InterfaceView(CLK:bits(1), X:uint(8), Y:uint(8), Z:uint(8)), Q:uint(8), W:uint(8))'}
-- 	kwargs={}
entity NestedIfc is
  port (
    CLK : in std_logic;
    OIFC_CLK : in std_logic;
    IIFCA_CLK : in std_logic;
    IIFCA_X : in unsigned(7 downto 0);
    IIFCA_Y : out unsigned(7 downto 0);
    IIFCA_Z : out unsigned(7 downto 0);
    IIFCB_CLK : in std_logic;
    IIFCB_X : in unsigned(7 downto 0);
    IIFCB_Y : out unsigned(7 downto 0);
    IIFCB_Z : out unsigned(7 downto 0);
    OIFC_Q : out unsigned(7 downto 0);
    OIFC_W : out unsigned(7 downto 0)
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

-- Entity "NestedInterfaceTest" is "NestedInterfaceTest" with:
-- 	args={'CLK': 'bits(1)', 'X': 'uint(8)', 'Y': 'uint(8)', 'Q': 'uint(8)'}
-- 	kwargs={}
architecture behavior of NestedInterfaceTest is
  signal INNER_Z : unsigned(7 downto 0);
  signal INNER1_Z : unsigned(7 downto 0);
  signal OUTER_W : unsigned(7 downto 0);
begin
  NestedIfc_1 : entity NestedIfc
  port map (
    CLK => CLK,
    OIFC_CLK => CLK,
    IIFCA_CLK => CLK,
    IIFCA_X => X + 1,
    IIFCA_Y => Y,
    IIFCA_Z => INNER_Z,
    IIFCB_CLK => CLK,
    IIFCB_X => X - 1,
    IIFCB_Y => Y,
    IIFCB_Z => INNER1_Z,
    OIFC_Q => Q,
    OIFC_W => OUTER_W
  );
end architecture;
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;
use ieee.float_pkg.all;
use std.textio.all;

library work;
use work.all;

-- Entity "NestedIfc" is "NestedIfc" with:
-- 	args={'CLK': 'bits(1)', 'OIFC': 'InterfaceView(an_int:17, CLK:bits(1), IIFCA:InterfaceView(CLK:bits(1), X:uint(8), Y:uint(8), Z:uint(8)), IIFCB:InterfaceView(CLK:bits(1), X:uint(8), Y:uint(8), Z:uint(8)), Q:uint(8), W:uint(8))'}
-- 	kwargs={}
architecture behavior of NestedIfc is
begin
  nested_process : process (CLK)
  begin
    if rising_edge(CLK) then
      OIFC_W <= IIFCA_X + 2;
      IIFCA_Z <= IIFCB_X - 17;
      IIFCB_Y <= IIFCA_X mod 16;
      OIFC_Q <= IIFCB_X + IIFCA_X;
    end if;
  end process;
end architecture;
