import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class LevelTrig(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(sens='A, B')
  def run():
    if A > B:
      XOUT = A + B
    else:
      XOUT = A - B


class EdgeTrig(X.Entity):

  PORTS = 'CLK, A, B, =XOUT'

  @X.hdl_process(sens='+CLK')
  def run():
    if A > B:
      XOUT = A + B
    else:
      XOUT = A - B


class TestOutType(unittest.TestCase):

  def test_level_trig(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), LevelTrig, inputs)

  def test_level_trig_regout(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkreg(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), LevelTrig, inputs)

  def test_edge_trig(self):
    inputs = dict(
      CLK=X.mkwire(X.BIT),
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), EdgeTrig, inputs)

  def test_edge_trig_regout(self):
    inputs = dict(
      CLK=X.mkwire(X.BIT),
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkreg(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), EdgeTrig, inputs)

