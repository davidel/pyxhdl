import logging
import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class ContextEnt(X.Entity):

  PORTS = (
    X.Port('A', X.IN),
    X.Port('B', X.IN),
    X.Port('XOUT', X.OUT),
  )

  @X.hdl_process(sens='A, B')
  def tester():
    c = X.mkwire(A.dtype)
    d = X.mkwire(A.dtype)

    with XL.context(delay=10):
      c = A - B
    with XL.context(delay=17, trans=True):
      d += A / B

    XOUT = c + A * B


class TestContext(unittest.TestCase):

  def test_context(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), ContextEnt, inputs)

