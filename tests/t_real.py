import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class RealEnt(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(sens='A, B')
  def run():
    add = mul = div = sub = X.mkreg(A.dtype)

    add = A + B
    mul = A * B
    div = A / B
    sub = A - B
    icplus = A + 3
    ifplus = A + 3.12
    XOUT = add + mul - div + sub * (icplus - ifplus)


class TestRealEnt(unittest.TestCase):

  def test_real(self):
    inputs = dict(
      A=X.mkwire(X.REAL),
      B=X.mkwire(X.REAL),
      XOUT=X.mkreg(X.REAL),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), RealEnt, inputs)

