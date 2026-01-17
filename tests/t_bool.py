import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class BasicBool(X.Entity):

  PORTS = 'A, B, C, =XOUT'

  @X.hdl_process(sens='A, B, C')
  def run():
    cc = X.mkreg(C.dtype)
    xx = X.mkvwire(X.Bits(4), '0b1001')
    if xx == XL.cast(A, xx.dtype):
      cc = C - 3
    else:
      cc = C + 17
    z = A and B
    XOUT = z or cc > 10


class TestBool(unittest.TestCase):

  def test_basic_bool(self):
    inputs = dict(
      A=X.mkwire(X.BOOL),
      B=X.mkwire(X.BOOL),
      C=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.BOOL),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), BasicBool, inputs)

