import pyxhdl as X
from pyxhdl import xlib as XL

from or_gate import OrGate
from not_gate import NotGate


class NorGate(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def run():
    OOUT = X.mkwire(XOUT.dtype)
    OrGate(A=A,
           B=B,
           XOUT=OOUT)
    NotGate(A=OOUT,
            XOUT=XOUT)

