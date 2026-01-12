import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class RamTest(X.Entity):

  PORTS = 'CLK, RST_N, RDEN, WREN, ADDR, IN_DATA, =OUT_DATA'

  ARGS = dict(RAM_SIZE=None)

  @X.hdl_process(sens='+CLK')
  def run():
    mem = X.mkreg(X.mkarray(IN_DATA.dtype, RAM_SIZE))

    if not RST_N:
      OUT_DATA = 0
    else:
      if WREN:
        mem[ADDR] = IN_DATA
      elif RDEN:
        OUT_DATA = mem[ADDR]


class TestRam(unittest.TestCase):

  def test_ram(self):
    inputs = dict(
      CLK=X.mkwire(X.BIT),
      RST_N=X.mkwire(X.BIT),
      RDEN=X.mkwire(X.BIT),
      WREN=X.mkwire(X.BIT),
      ADDR=X.mkwire(X.Bits(12)),
      IN_DATA=X.mkwire(X.Bits(16)),
      OUT_DATA=X.mkreg(X.Bits(16)),

      RAM_SIZE=3 * 1024,
    )

    tu.run(self, tu.test_name(self, pyu.fname()), RamTest, inputs)

