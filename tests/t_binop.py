import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class BinOp(X.Entity):

  PORTS = (
    X.Port('A', X.Port.IN),
    X.Port('B', X.Port.IN),
    X.Port('XOUT', X.Port.OUT),
  )

  @X.hdl_process(sens='A, B')
  def run():
    add = mul = div = sub = X.mkreg(A.dtype)

    add = A + B
    mul = A * B
    div = A / B
    sub = A - B
    xmod = A % B
    conc = A @ B
    lshift = conc << (2 + 4)
    rshift = conc >> (2 + 4)
    kshift = lshift ^ rshift
    XOUT = add + mul - div + sub - xmod + conc - kshift


class TestBinOp(unittest.TestCase):

  def test_binop_wire_wire(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), BinOp, inputs)

  def test_binop_wire_wire_8_16(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT16),
      XOUT=X.mkwire(X.UINT16),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), BinOp, inputs)

  def test_binop_wire_reg(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkreg(X.UINT8),
      XOUT=X.mkwire(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), BinOp, inputs)

  def test_binop_wire_reg_8_16(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkreg(X.UINT16),
      XOUT=X.mkwire(X.UINT16),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), BinOp, inputs)

