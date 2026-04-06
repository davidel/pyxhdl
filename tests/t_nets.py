import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class NetsTest(X.Entity):

  PORTS = 'CLK, A, B, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root():
    ROOT_REG = X.mkreg(A.dtype)
    ROOT_WIRE = X.mkwire(A.dtype)

    ROOT_WIRE = A * B

  @X.hdl_process(sens='A, B')
  def combo():
    COMBO_WIRE = X.mkwire(A.dtype)

    if A > B:
      COMBO_WIRE = A + B - ROOT_WIRE
    else:
      COMBO_WIRE = A - B + ROOT_WIRE

    ROOT_REG = COMBO_WIRE

  @X.hdl_process(sens='+CLK')
  def clocker():
    if B == 1:
      XOUT = ROOT_REG


class TestNets(unittest.TestCase):

  def test_nets_wire(self):
    inputs = dict(
      CLK=X.mkreg(X.BIT),
      A=X.mkreg(X.UINT8),
      B=X.mkreg(X.UINT8),
      XOUT=X.mkreg(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), NetsTest, inputs)

  def test_nets_reg(self):
    inputs = dict(
      CLK=X.mkwire(X.BIT),
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), NetsTest, inputs)

