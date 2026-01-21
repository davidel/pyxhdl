import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class ForEnt(X.Entity):

  PORTS = (
    X.Port('A', X.Port.IN),
    X.Port('B', X.Port.IN),
    X.Port('XOUT', X.Port.OUT),
  )

  ARGS = dict(count=1)

  @X.hdl_process(sens='A, B')
  def run():
    temp = XL.mkvreg(A.dtype, 1)
    for _ in range(count):
      temp += 1

    XOUT = temp * A - B


@X.hdl
def _xgen(a, b, n):
  for i in range(n):
    if i % 2 == 0:
      yield a + b
    else:
      yield a - b


class GenForEnt(X.Entity):

  PORTS = (
    X.Port('A', X.Port.IN),
    X.Port('B', X.Port.IN),
    X.Port('XOUT', X.Port.OUT),
  )

  ARGS = dict(count=1)

  @X.hdl_process(sens='A, B')
  def run():
    temp = XL.mkvreg(A.dtype, 1)
    for v in _xgen(A, B, count):
      temp += v

    XOUT = temp - 17


class TestFor(unittest.TestCase):

  def test_for(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT8),

      count=4,
    )

    tu.run(self, tu.test_name(self, pyu.fname()), ForEnt, inputs)

  def test_gen_for(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT8),

      count=4,
    )

    tu.run(self, tu.test_name(self, pyu.fname()), GenForEnt, inputs)

