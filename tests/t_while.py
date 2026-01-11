import logging
import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class WhileEnt(X.Entity):

  PORTS = (
    X.Port('A', X.IN),
    X.Port('B', X.IN),
    X.Port('XOUT', X.OUT),
  )

  ARGS = dict(count=1)

  @X.hdl_process(sens='A, B')
  def run():
    temp = XL.mkvwire(A.dtype, 1)
    i = 0
    while i < count:
      temp += 1
      i += 1

    XOUT = temp * A - B


class TestWhile(unittest.TestCase):

  def test_while(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT8),

      count=4,
    )

    tu.run(self, tu.test_name(self, pyu.fname()), WhileEnt, inputs)

  def test_while_regout(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkreg(X.UINT8),

      count=4,
    )

    tu.run(self, tu.test_name(self, pyu.fname()), WhileEnt, inputs)

