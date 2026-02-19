import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


@X.hdl
def match_return_result(v, a, b):
  result = X.mkwire(a.dtype)

  match v:
    case 17:
      result = a + 1
    case 21:
      result = a + b
    case 34:
      result = a - b
    case _:
      result = a * b

  return result


@X.hdl
def match_return(v, a, b):
  match v:
    case 17:
      return a + 1
    case 21:
      return a + b
    case 34:
      return a - b
    case _:
      return a * b


class MatchEnt(X.Entity):

  PORTS = (
    X.Port('A', X.Port.IN),
    X.Port('B', X.Port.IN),
    X.Port('XOUT', X.Port.OUT),
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


class MatchReturnResultEnt(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(sens='A, B')
  def tester():
    XOUT = match_return_result(A, A, B)


class MatchReturnEnt(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(sens='A, B')
  def tester():
    XOUT = match_return(A, A, B)


class TestMatch(unittest.TestCase):

  def test_match(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), MatchEnt, inputs)

  def test_match_return_result(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), MatchReturnResultEnt, inputs)

  def test_match_return(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), MatchReturnEnt, inputs)
