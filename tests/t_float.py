import logging
import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class FloatEnt(X.Entity):

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
    if A.is_nan() or A.is_inf():
      add += 1.0
    XOUT = add + mul - div + sub * (icplus - ifplus)


class TestFloatEnt(unittest.TestCase):

  def test_float(self):
    inputs = dict(
      A=X.mkwire(X.Float(32)),
      B=X.mkwire(X.Float(32)),
      XOUT=X.mkwire(X.Float(16)),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), FloatEnt, inputs)

