import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class BigInt(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(proc_mode='comb')
  def big_int():
    XOUT = A + B - (2**45 - 1)


class TestBigInt(unittest.TestCase):

  def test_big_int(self):
    inputs = dict(
      A=X.mkwire(X.Uint(64)),
      B=X.mkwire(X.Uint(64)),
      XOUT=X.mkwire(X.Uint(64)),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), BigInt, inputs)

