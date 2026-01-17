import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class CombProcess(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(proc_mode='comb')
  def comby():
    XOUT = A - 7 * B


class TestCombProcess(unittest.TestCase):

  def test_comb(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkreg(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), CombProcess, inputs)

