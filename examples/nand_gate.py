import pyxhdl as X
from pyxhdl import xlib as XL

from and_gate import AndGate
from not_gate import NotGate


class NandGate(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def run():
    OOUT = X.mkwire(XOUT.dtype)
    AndGate(A=A,
            B=B,
            XOUT=OOUT)
    NotGate(A=OOUT,
            XOUT=XOUT)

