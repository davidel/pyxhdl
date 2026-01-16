import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class Switcher(X.Entity):

  PORTS = 'SEL, DIN, =SEL_DOUT, SEL_DIN, =DOUT'

  @X.hdl_process(sens='SEL, DIN, SEL_DIN')
  def switch():
    N = SEL_DIN.dtype.array_shape[0]

    SEL_DOUT = X.bitfill('X', SEL_DOUT.dtype.nbits)
    DOUT = X.bitfill('X', DOUT.dtype.nbits)

    for i in range(N):
      if SEL == i:
        SEL_DOUT[i] = DIN
        DOUT = SEL_DIN[i]


class TestSwitcher(unittest.TestCase):

  def test_basic_bits(self):
    inputs = dict(
      SEL=X.mkwire(X.Bits(3)),
      DIN=X.mkwire(X.Bits(16)),
      SEL_DOUT=X.mkwire(X.mkarray(X.Bits(16), 8)),
      SEL_DIN=X.mkwire(X.mkarray(X.Bits(16), 8)),
      DOUT=X.mkwire(X.Bits(16)),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), Switcher, inputs)

