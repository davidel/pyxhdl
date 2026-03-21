import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class LocalFn(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    import random

    def testfn(a):
      return a + random.randint(21, 21)

    XOUT = A + B + testfn(17)


class TestLocalFn(unittest.TestCase):

  def test_local_fn(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkreg(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), LocalFn, inputs)

