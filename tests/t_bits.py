import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class BasicBits(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(sens='A, B')
  def run():
    z = X.mkreg(X.Uint(4))
    w = X.mkwire(X.Uint(4))
    cc = XL.cast(A, X.Uint(2)) + XL.cast(B, X.Uint(1))
    z = cc + 3
    w = z
    cb = A @ B
    XOUT = z * 17 - w


class Recast(X.Entity):

  PORTS = (
    X.Port('A', X.IN),
    X.Port('B', X.IN),
    X.Port('XOUT', X.OUT),
  )

  @X.hdl_process(sens='A, B')
  def run():
    auto = X.mkreg(A.dtype)
    auto = A + B
    auto = A * B
    XOUT = auto / 4


class TestBits(unittest.TestCase):

  def test_basic_bits(self):
    inputs = dict(
      A=X.mkwire(X.BIT),
      B=X.mkwire(X.BIT),
      XOUT=X.mkwire(X.Bits(4)),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), BasicBits, inputs)

  def test_recast(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT4),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), Recast, inputs)

