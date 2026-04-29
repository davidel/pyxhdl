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


class GatherTest(X.Entity):

  PORTS = 'A, =XOUT'

  @X.hdl_process(sens='A')
  def run():
    g1 = XU.gather(A, 0, A.dtype.nbits, step=2)
    g2 = XU.gather(A, 1, A.dtype.nbits, step=2)

    XOUT = g1 @ g2


class TestXUtils(unittest.TestCase):

  def test_snap(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkreg(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), SnapTest, inputs)

  def test_gather(self):
    inputs = dict(
      A=X.mkwire(X.Bits(32)),
      XOUT=X.mkreg(X.Bits(32)),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), GatherTest, inputs)

