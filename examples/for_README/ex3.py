import py_misc_utils.template_replace as pytr

import pyxhdl as X
from pyxhdl import xlib as XL

class And(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def run():
    XOUT = A & B


_TEMPLATE = """
And(A=A[$i], B=B[$i], XOUT=XOUT[$i])
"""

class Ex3(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def run():
    for i in range(A.dtype.nbits):
      code = pytr.template_replace(_TEMPLATE, vals=dict(i=i))
      XL.xexec(code)
