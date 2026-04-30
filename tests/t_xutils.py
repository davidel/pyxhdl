import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL
from pyxhdl import xutils as XU

import test_utils as tu


class SnapTest(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(sens='A, B')
  def run():
    snap_value = XU.snap(A + B)

    XOUT = snap_value


class SelectTest(X.Entity):

  PORTS = 'A, =XOUT'

  @X.hdl_process(sens='A')
  def run():
    s1 = XU.select(A, range(0, A.dtype.nbits, 2))
    s2 = XU.select(A, range(1, A.dtype.nbits, 2))

    XOUT = s1 @ s2


class SplitTest(X.Entity):

  PORTS = 'A, =XOUT'

  @X.hdl_process(sens='A')
  def run():
    s1, s2, s3 = XU.split(A, 4, 5, A.dtype.nbits - 10, base=1)

    XOUT = s3 @ s1 @ s2


class TestXUtils(unittest.TestCase):

  def test_snap(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkreg(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), SnapTest, inputs)

  def test_select(self):
    inputs = dict(
      A=X.mkwire(X.Bits(32)),
      XOUT=X.mkreg(X.Bits(32)),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), SelectTest, inputs)

  def test_split(self):
    inputs = dict(
      A=X.mkwire(X.Bits(32)),
      XOUT=X.mkreg(X.Bits(32)),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), SplitTest, inputs)

