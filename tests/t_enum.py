import enum
import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class Ops(enum.IntEnum):
  A_OP = 17
  B_OP = enum.auto()
  C_OP = enum.auto()


class EnumEnt(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(sens='A, B')
  def tester():
    match A:
      case Ops.A_OP:
        XOUT = A + 1
      case Ops.B_OP:
        XOUT = A + B
      case Ops.C_OP:
        XOUT = A - B
      case _:
        XOUT = A * B


class TestEnum(unittest.TestCase):

  def test_enum(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkreg(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), EnumEnt, inputs)

