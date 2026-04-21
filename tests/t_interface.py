import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class MyInterface(X.Interface):

  FIELDS = 'X:u16, Y:u16=0'

  IPORT = 'X, Y, Q, =Z'

  def __init__(self, **kwargs):
    super().__init__('MYIFC', **kwargs)
    if 'Z' not in kwargs:
      self.mkfield('Z', 'u16')

  @X.hdl
  def reset(self):
    self.X = 17
    self.Y = 21


class IfcEnt(X.Entity):

  PORTS = f'A, B, *IFC:{__name__}.MyInterface.IPORT'

  @X.hdl_process(sens='A, B, IFC.X, IFC.Y, IFC.Q')
  def sensif(self):
    temp1 = A & B
    temp2 = A ^ B

    IFC.Z = temp1 | temp2 | (IFC.X + IFC.Y - IFC.Q)


class InterfaceTest(X.Entity):

  PORTS = 'CLK, RST_N, A, B, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    self.ifc = MyInterface(Q=A + 1)

    IfcEnt(A=A,
           B=B,
           IFC=self.ifc)

  @X.hdl_process(sens='+CLK')
  def run(self):
    if not RST_N:
      XOUT = 0
      self.ifc.reset()
    else:
      self.ifc.X += self.ifc.Q
      self.ifc.Y -= 1
      XOUT = self.ifc.Q + 3


class InterfaceArrayTest(X.Entity):

  PORTS = 'CLK, RST_N, A, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    self.ifc = MyInterface(Q=A[0], Z=XOUT[0])

    IfcEnt(A=A[0],
           B=A[1],
           IFC=self.ifc)

  @X.hdl_process(sens='+CLK')
  def run(self):
    if not RST_N:
      XOUT[1] = 0
      self.ifc.reset()
    else:
      self.ifc.X -= self.ifc.Q
      self.ifc.Y += 1
      XOUT[1] = self.ifc.Q * 3


class InnerIfc(X.Interface):

  IPORT = 'CLK, X, =Y, =Z'

  def __init__(self, clk, x, y, **kwargs):
    super().__init__('INNER', **kwargs)
    self.mkfield('CLK', clk)
    self.mkfield('X', x)
    self.mkfield('Y', y)
    self.mkfield('Z', X.Uint(y.dtype.nbits))


class OuterIfc(X.Interface):

  IPORT = f'CLK, *IIFCA:{__name__}.InnerIfc.IPORT, *IIFCB:{__name__}.InnerIfc.IPORT, =Q, =W'

  def __init__(self, clk, iifca, iifcb, q, **kwargs):
    super().__init__('OUTER', **kwargs)
    self.mkfield('CLK', clk)
    self.mkfield('IIFCA', iifca)
    self.mkfield('IIFCB', iifcb)
    self.mkfield('Q', q)
    self.mkfield('W', X.Uint(q.dtype.nbits))


class NestedIfc(X.Entity):

  PORTS = f'CLK, *OIFC:{__name__}.OuterIfc.IPORT'

  @X.hdl_process(sens='+CLK')
  def nested_process(self):
    OIFC.W = OIFC.IIFCA.X + 2
    OIFC.IIFCA.Z = OIFC.IIFCB.X - OIFC.an_int
    OIFC.IIFCB.Y = OIFC.IIFCA.X % 16
    OIFC.Q = OIFC.IIFCB.X + OIFC.IIFCA.X


class NestedInterfaceTest(X.Entity):

  PORTS = 'CLK, X, =Y, =Q'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    self.inner_ifca = InnerIfc(CLK, X + 1, Y)
    self.inner_ifcb = InnerIfc(CLK, X - 1, Y)

    self.outer_ifc = OuterIfc(CLK, self.inner_ifca, self.inner_ifcb, Q,
                              an_int=17)

    NestedIfc(CLK=CLK,
              OIFC=self.outer_ifc)


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

  def test_interface_array(self):
    inputs = dict(
      CLK=X.mkwire(X.BIT),
      RST_N=X.mkwire(X.BIT),
      A=X.mkwire(X.mkarray(X.UINT8, 2)),
      XOUT=X.mkreg(X.mkarray(X.UINT8, 2)),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), InterfaceArrayTest, inputs)

  def test_nested(self):
    inputs = dict(
      CLK=X.mkwire(X.BIT),
      X=X.mkwire(X.UINT8),
      Y=X.mkwire(X.UINT8),
      Q=X.mkwire(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), NestedInterfaceTest, inputs)

