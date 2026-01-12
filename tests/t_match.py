import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class MatchEnt(X.Entity):

  PORTS = (
    X.Port('A', X.IN),
    X.Port('B', X.IN),
    X.Port('XOUT', X.OUT),
  )

  @X.hdl_process(sens='A, B')
  def tester():
    match A:
      case 17:
        XOUT = A + 1
      case 21:
        XOUT = A + B
      case 34:
        XOUT = A - B
      case _:
        XOUT = A * B


class TestMatch(unittest.TestCase):

  def test_match(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), MatchEnt, inputs)

