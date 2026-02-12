library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity ExEntity is
  generic (
    NBITS : integer := 8;
    DELTA : integer := 16
  );
  port (
    IN_A : in unsigned;
    IN_B : in unsigned;
    OUT_DATA : out unsigned
  );
end entity;

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

architecture behavior of ExEntity is
begin
  proc : process (IN_A, IN_B)
  begin
    OUT_DATA <= IN_A + IN_B - to_unsigned(DELTA, IN_A'length);
  end process;
end architecture;
