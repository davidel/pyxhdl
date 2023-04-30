import logging
import math
import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class IntReal(X.Entity):

  PORTS = (
    X.Port('A', X.IN),
    X.Port('B', X.IN),
    X.Port('XOUT', X.OUT),
  )

  @X.hdl_process(sens='A')
  def test():
    idx = XL.mkvreg(X.INT, XOUT.dtype.shape[0] - 1)

    z = A + B
    XOUT[idx] = z * 17 - 3.14
    idx -= 1
    XOUT[idx] = z / 21.0 + math.e
    idx -= 1
    XOUT[idx] = z + idx


class TestIntReal(unittest.TestCase):

  def test(self):
    inputs = dict(
      A=X.mkwire(X.INT),
      B=X.mkwire(X.REAL),
      XOUT=X.mkreg(X.mkarray(X.REAL, 4)),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), IntReal, inputs)

