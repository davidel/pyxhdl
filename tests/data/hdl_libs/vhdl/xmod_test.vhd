library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.all;

entity xmod_test is
  port (
    A : in unsigned(7 downto 0);
    B : in unsigned(7 downto 0);
    XOUT : out unsigned(7 downto 0)
  );
end entity;

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.all;

architecture behavior of xmod_test is
begin
  run : process (A, B)
  begin
    XOUT <= A + B;
  end process;
end architecture;
