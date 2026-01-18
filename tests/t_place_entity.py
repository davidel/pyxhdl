import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


_EXTERN_VHDL = """
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;
use ieee.float_pkg.all;

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
use ieee.math_real.all;
use ieee.float_pkg.all;

architecture behavior of ExEntity is
begin
  proc : process (IN_A, IN_B)
  begin
    OUT_DATA <= IN_A + IN_B - to_unsigned(DELTA, IN_A'length);
  end process;
end architecture;
"""

_EXTERN_VERILOG = """
module ExEntity(IN_A, IN_B, OUT_DATA);
  parameter integer NBITS = 8;
  parameter integer DELTA = 16;

  input logic [NBITS - 1: 0] IN_A;
  input logic [NBITS - 1: 0] IN_B;
  output logic [NBITS - 1: 0] OUT_DATA;

  assign OUT_DATA = IN_A + IN_B - DELTA;
endmodule
"""


class EnternalEntity(X.Entity):

  PORTS = 'IN_A:u*, IN_B:u*, =OUT_DATA:u*'
  NAME = 'ExEntity'


class PlaceEntity(X.Entity):

  PORTS = 'A:u*, B:u*, =XOUT:u*'

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    XL.register_module('ExEntity', {'vhdl': _EXTERN_VHDL, 'verilog': _EXTERN_VERILOG})

  @X.hdl_process(sens='A, B', kind=X.ROOT_PROCESS)
  def run():
    # The ExEntity will have to be defined in backend specific library files
    # to be loaded within PyXHDL (see "Loading External Libraries" within the README
    # file).
    # In this example we just define it locally using XL.register_module(), in order
    # to shut warnings down when we verify test-generated code.
    EnternalEntity(IN_A=A, IN_B=B, OUT_DATA=XOUT,
                   _P=dict(NBITS=A.dtype.nbits, DELTA=7))


class TestPlaceEntity(unittest.TestCase):

  def test_place_entity(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), PlaceEntity, inputs)

