import pyxhdl as X
from pyxhdl import xlib as XL


class TestIfc(X.Interface):

  FIELDS = 'X:u16, Y:u16=0'

  IPORT = 'CLK, RST_N, +X, +Y, =XOUT'

  def __init__(self, clk, rst_n, xout, **kwargs):
    super().__init__('TEST', **kwargs)
    self.mkfield('CLK', clk)
    self.mkfield('RST_N', rst_n)
    self.mkfield('XOUT', xout)


class IfcEnt(X.Entity):

  PORTS = f'*IFC:{__name__}.TestIfc.IPORT, A'

  @X.hdl_process(sens='+IFC.CLK')
  def run(self):
    if IFC.RST_N != 1:
      IFC.X = 1
      IFC.Y = 0
      IFC.XOUT = 0
    else:
      IFC.XOUT = A * IFC.X + IFC.Y - IFC.an_int
      IFC.X += 1
      IFC.Y += 2


class IfcTest(X.Entity):

  PORTS = 'CLK, RST_N, A, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    self.ifc = TestIfc(CLK, RST_N, XOUT,
                       an_int=17)

    IfcEnt(IFC=self.ifc,
           A=A)

