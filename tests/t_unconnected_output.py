import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class TestEntity(X.Entity):

  PORTS = 'A, B, =XOUT, =UNCONN'

  @X.hdl_process(sens='A, B', kind=X.ROOT_PROCESS)
  def run():
    XOUT = A - B
    UNCONN = A + B


class OpenOut(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root():
    TestEntity(A=A,
               B=B,
               XOUT=XOUT,
               UNCONN=X.mknone(XOUT.dtype))


class TestUnconnectedOut(unittest.TestCase):

  def test_unconnected_out(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkreg(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), OpenOut, inputs)

