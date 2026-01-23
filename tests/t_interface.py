import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class MyInterface(X.Interface):

  FIELDS = 'X:u16, Y:u16=0'

  IPORT = 'X, Y, =Z'

  def __init__(self):
    super().__init__('MYIFC')
    self.mkfield('Z', 'u16')

  @X.hdl
  def reset(self):
    self.X = 17
    self.Y = 21


class IfcEnt(X.Entity):

  PORTS = f'A, B, *IFC:{__name__}.MyInterface.IPORT'

  @X.hdl_process(sens='A, B, IFC.X, IFC.Y')
  def sensif(self):
    temp1 = A & B
    temp2 = A ^ B

    IFC.Z = temp1 | temp2 | (IFC.X + IFC.Y)


class InterfaceTest(X.Entity):

  PORTS = 'CLK, RST_N, A, B, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    self.ifc = MyInterface()

    IfcEnt(A=A,
           B=B,
           IFC=self.ifc)

  @X.hdl_process(sens='+CLK')
  def run(self):
    if not RST_N:
      XOUT = 0
      self.ifc.reset()
    else:
      pass


class TestInterface(unittest.TestCase):

  def test_interface(self):
    inputs = dict(
      CLK=X.mkwire(X.BIT),
      RST_N=X.mkwire(X.BIT),
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),

      XOUT=X.mkreg(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), InterfaceTest, inputs)

