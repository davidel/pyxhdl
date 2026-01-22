import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class NamedInit(X.Entity):

  PORTS = 'CLK, A, B, =XOUT'

  @X.hdl_process(sens='+CLK')
  def named_init():
    temp = X.mkvwire(A.dtype, 0, name='named')

    temp += 1
    XOUT = A + B - temp


class TestNamedInit(unittest.TestCase):

  def test_named_init(self):
    inputs = dict(
      CLK=X.mkwire(X.BIT),
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), NamedInit, inputs)

