import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class AttributesTest(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(sens='A, B')
  def run(self):

    COMMON_ATTRS = {
      '$common': {
        'common_string': 'a string',
        'common_int': 17,
        'common_float': 17.21,
      },
    }

    wcomm = X.mkwire(A.dtype, attributes=COMMON_ATTRS)

    COMMON_VHDL_ATTRS = {
      '$common': {
        'common_int': 21,
      },
      'vhdl': {
        'vhdl_string': 'a string',
        'vhdl_int': 21,
        'vhdl_float': 21.17,
      },
    }

    wcomm_vhd = X.mkwire(A.dtype, attributes=COMMON_VHDL_ATTRS)

    COMMON_VERILOG_ATTRS = {
      '$common': {
        'common_string': 'another string',
      },
      'verilog': {
        'verilog_string': 'a SV string',
        'verilog_int': 3,
        'verilog_float': 11.65,
      },
    }

    wcomm_ver = X.mkwire(A.dtype, attributes=COMMON_VERILOG_ATTRS)

    wcomm = A + B
    wcomm_vhd = A - B
    wcomm_ver = A * B

    XOUT = wcomm - wcomm_vhd + wcomm_ver


class TestAttributes(unittest.TestCase):

  def test_attributes(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkreg(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), AttributesTest, inputs)

