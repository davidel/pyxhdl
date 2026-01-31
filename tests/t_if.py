import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class IfEnt(X.Entity):

  PORTS = (
    X.Port('A', X.Port.IN),
    X.Port('B', X.Port.IN),
    X.Port('XOUT', X.Port.OUT),
  )

  ARGS = dict(kwarg=-1)

  @X.hdl_process(sens='A, B')
  def run():
    # The "else" branch should be droppped.
    temp = X.mkwire(A.dtype)
    if kwarg > 10:
      temp = A
    else:
      temp = B

    if A > B:
      temp += A
    elif B > A:
      temp -= B
    elif B == A:
      temp *= B
    else:
      temp = 0

    if A > B:
      temp -= A
    elif A < B:
      temp += A
    else:
      if A == B:
        temp /= A

      temp += 1

    if kwarg > 5 and A > B:
      temp -= 1

    XOUT = temp


class TestIf(unittest.TestCase):

  def test_if_wire_wire(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT8),

      kwarg=17,
    )

    tu.run(self, tu.test_name(self, pyu.fname()), IfEnt, inputs)


  def test_if_wire_wire_8_16(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT16),
      XOUT=X.mkwire(X.UINT16),

      kwarg=3,
    )

    tu.run(self, tu.test_name(self, pyu.fname()), IfEnt, inputs)

