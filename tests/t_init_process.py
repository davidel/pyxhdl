import logging
import unittest

import numpy as np

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class InitProcess(X.Entity):

  PORTS = (
    X.Port('A', X.IN),
    X.Port('B', X.IN),
    X.Port('XOUT', X.OUT),
  )

  ARGS = dict(init=None)

  @X.hdl_process(kind=X.INIT_PROCESS)
  def init():
    arr = X.mkwire(X.mkarray(A.dtype, 4, 4))
    zarr = XL.mkvwire(X.mkarray(A.dtype, 4, 4), 1)
    for i in range(init.shape[0]):
      for j in range(init.shape[1]):
        arr[i, j] = init[i, j]

  @X.hdl_process(sens='A, B')
  def run():
    temp = XL.mkvreg(A.dtype, 21)
    XOUT = A - 3 * B - temp * arr[1, 2] + 11 * zarr[2, 3]


class TestInitProcess(unittest.TestCase):

  def test_init(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT8),

      init=np.arange(0, 16, dtype=np.uint8).reshape(4, 4),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), InitProcess, inputs)

