import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class ExtraArgs(X.Entity):

  PORTS = (
    X.Port('A', X.Port.IN),
    X.Port('B', X.Port.IN),
    X.Port('XOUT', X.Port.OUT),
  )

  ARGS = dict(myarg1=0, myarg2=0)

  @X.hdl_process(sens='A, B')
  def run():
    XOUT = A * B + myarg1 - myarg2



class TestKwargs(unittest.TestCase):

  def test_basic(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT8),

      myarg1=17,
      myarg2=21,
    )

    tu.run(self, tu.test_name(self, pyu.fname()), ExtraArgs, inputs)

