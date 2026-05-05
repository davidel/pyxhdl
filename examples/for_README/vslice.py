import pyxhdl as X


class VarSlice(X.Entity):

  PORTS = 'A=b16, B=u4, =XOUT=b4'

  @X.hdl_process(sens='A, B')
  def var_slice():
    XOUT = A[B + 1::4]

