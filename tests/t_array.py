import unittest

import numpy as np

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class MatMult(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(sens='A, B')
  def mat_mult():
    for i in range(A.dtype.shape[0]):
      for j in range(B.dtype.shape[1]):
        temp = 0
        for k in range(B.dtype.shape[0]):
          temp += A[i, k] * B[k, j]

        XOUT[i, j] = temp


class ArrayTestEnt(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(sens='A, B')
  def slicing():
    tempa = A[1, 0, 4: 8]
    tempb = B[0, 1, : 4]

    XOUT = tempa + tempb

  @X.hdl_process(sens='A, B')
  def assign_slicing():
    XOUT[: 4] = A[1, 0, 4: 8]
    XOUT[4: 8] = B[0, 1, : 4]

  @X.hdl_process(sens='A, B')
  def indexing():
    idx = A[0, 1]
    XOUT = B[0, idx]

  @X.hdl_process(sens='A, B')
  def np_init():
    ar = XL.mkvreg(X.mkarray(X.UINT16, 3, 2, 4), np.arange(0, 24, dtype=np.uint16).reshape(3, 2, 4))
    ar_const = XL.mkvreg(X.mkarray(X.UINT16, 3, 2, 4), np.arange(0, 24, dtype=np.uint16).reshape(3, 2, 4), const=True)

    XOUT = B[0, 1] - ar[1][0][1] + ar_const[2][1][2]


class ArrayAssignTestEnt(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(sens='A, B')
  def assign_element():
    XOUT[1] = B[0]


class ArrayShiftSliceEnt(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(sens='A, B')
  def var_slice():
    tmp = A >> B
    XOUT = tmp[: 4]


class ArrayVarSliceEnt(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(sens='A, B')
  def var_slice():
    XOUT = A[B + 1::4] + A[B + 2::-3]


class TestArray(unittest.TestCase):

  def test_matmul(self):
    inputs = dict(
      A=X.mkwire(X.Uint(4, 4, 16)),
      B=X.mkwire(X.Uint(4, 4, 16)),
      XOUT=X.mkwire(X.Uint(4, 4, 16)),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), MatMult, inputs)

  def test_array(self):
    inputs = dict(
      A=X.mkwire(X.Uint(2, 2, 16)),
      B=X.mkwire(X.Uint(2, 2, 16)),
      XOUT=X.mkwire(X.UINT16),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), ArrayTestEnt, inputs)

  def test_assign(self):
    inputs = dict(
      A=X.mkwire(X.Uint(2, 2, 16)),
      B=X.mkwire(X.Sint(2, 2, 16)),
      XOUT=X.mkwire(X.Sint(2, 2, 16)),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), ArrayAssignTestEnt, inputs)

  def test_shift_slice(self):
    inputs = dict(
      A=X.mkwire(X.Uint(32)),
      B=X.mkwire(X.Uint(4)),
      XOUT=X.mkwire(X.Bits(4)),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), ArrayShiftSliceEnt, inputs)

  def test_var_slice(self):
    inputs = dict(
      A=X.mkwire(X.Uint(32)),
      B=X.mkwire(X.Uint(4)),
      XOUT=X.mkwire(X.Bits(4)),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), ArrayVarSliceEnt, inputs)

