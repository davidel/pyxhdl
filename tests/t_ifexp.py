import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class IfExp(X.Entity):

  PORTS = (
    X.Port('A', X.Port.IN),
    X.Port('B', X.Port.IN),
    X.Port('XOUT', X.Port.OUT),
  )

  @X.hdl_process(sens='A, B')
  def run():
    XOUT = A if A > B else B + 1


class TestIfExp(unittest.TestCase):

  def test_ifexp_wire_wire(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), IfExp, inputs)


  def test_ifexp_wire_wire_8_16(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT16),
      XOUT=X.mkwire(X.UINT16),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), IfExp, inputs)


