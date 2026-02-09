import os
import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xcall as XC
from pyxhdl import xlib as XL

import test_utils as tu


xmod_call = XC.create_function(
  'xmod_call',
  X.Emitter.xmod_resolve('xmod_test', 'xmod_test', 0),
  fnsig='u*, u*',
  dtype=XC.argn_dtype(0))


class XModCallEnt(X.Entity):

  PORTS = 'A, B, =XOUT'

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    xmod_path = os.path.join(os.path.dirname(__file__),
                             'data', 'hdl_libs', 'xmod_test.yaml')

    self.xmod = XL.load_extern_module(xmod_path)

  @X.hdl_process(sens='A, B')
  def run(self):
    XOUT = xmod_call(A, B)


class TestXModCall(unittest.TestCase):

  def test_xmod_call(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkreg(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), XModCallEnt, inputs)

