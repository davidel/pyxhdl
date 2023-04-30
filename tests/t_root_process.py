import logging
import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class RootProcess(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(sens='A, B', kind=X.ROOT_PROCESS)
  def run():
    temp = XL.mkvwire(A.dtype, 21)
    XOUT = A - 3 * B - temp


class TestRootProcess(unittest.TestCase):

  def test_root(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), RootProcess, inputs)

