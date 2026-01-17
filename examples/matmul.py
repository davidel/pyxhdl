# This is just an example of a trivial MatMul unit, in order to test PyXHDL
# and its inter-operability with numpy arrays.
import logging

import numpy as np

import pyxhdl as X
from pyxhdl import xlib as XL


class MatMult(X.Entity):

  PORTS = 'CLK, RESET, A, B, A_ROW, MMITER, B_COL, COMPUTE, =XOUT'
  ARGS = dict(tilesize=8)

  @X.hdl_process(sens='+CLK')
  def mat_mult():
    i_mmiter = X.mkvreg(X.INT, 0)
    iarow = X.mkvreg(X.INT, 0)
    ibcol = X.mkvreg(X.INT, 0)

    if RESET == 1:
      XOUT = 0
    elif COMPUTE == 1:
      i_mmiter = MMITER
      for i in range(tilesize):
        iarow = A_ROW + i
        for j in range(tilesize):
          ibcol = B_COL + j
          temp = A[iarow, i_mmiter] * B[i_mmiter, ibcol]
          for k in range(1, tilesize):
            temp += A[iarow, i_mmiter + k] * B[i_mmiter + k, ibcol]

          XOUT[iarow, ibcol] += temp


class MMUnit(X.Entity):

  PORTS = 'CLK, RESET, INFEED, OUTFEED, AROW, BROW, COMPUTE, =READY, =CROW'
  ARGS = dict(tilesize=8)

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root():
    N = AROW.dtype.array_shape[-1]
    tsize = min(tilesize, N)
    assert N % tsize == 0

    amat = X.mkwire(AROW.dtype.new_shape(N, N, AROW.dtype.nbits))
    bmat = X.mkwire(BROW.dtype.new_shape(N, N, BROW.dtype.nbits))
    a_row = X.mkvwire(X.UINT8, 0)
    mmiter = X.mkvwire(X.UINT8, 0)
    b_col = X.mkvwire(X.UINT8, 0)
    cmat = X.mkwire(CROW.dtype.new_shape(N, N, CROW.dtype.nbits))
    mmcompute = X.mkvwire(COMPUTE.dtype, 0)

    MatMult(
      CLK=CLK,
      RESET=RESET,
      A=amat,
      B=bmat,
      A_ROW=a_row,
      MMITER=mmiter,
      B_COL=b_col,
      COMPUTE=mmcompute,
      XOUT=cmat,
      tilesize=tsize)

  # States
  INIT = 0
  COMPUTING = 1

  @X.hdl_process(sens='+CLK')
  def main():
    rowidx = XL.mkreg(X.INT)
    state = XL.mkreg(X.UINT4)

    if RESET == 1:
      READY = 0
      rowidx = 0
      mmcompute = 0
      a_row, mmiter, b_col = 0, 0, 0
      state = MMUnit.INIT
    elif state == MMUnit.COMPUTING:
      N = AROW.dtype.array_shape[-1]
      tsize = min(tilesize, N)
      LIMIT = N - tsize
      if mmiter == LIMIT:
        mmiter = 0
        if a_row == LIMIT:
          a_row = 0
          if b_col == LIMIT:
            state = MMUnit.INIT
            mmcompute = 0
            READY = 1
          else:
            b_col += tsize
        else:
          a_row += tsize
      else:
        mmiter += tsize
    elif INFEED == 1:
      for n in range(AROW.dtype.array_shape[-1]):
        amat[rowidx, n] = AROW[n]
      for n in range(BROW.dtype.array_shape[-1]):
        bmat[rowidx, n] = BROW[n]

      rowidx += 1
    elif COMPUTE == 1:
      READY = 0
      state = MMUnit.COMPUTING
      rowidx = 0
      a_row, mmiter, b_col = 0, 0, 0
      mmcompute = 1
    elif OUTFEED == 1:
      for n in range(CROW.dtype.array_shape[-1]):
        CROW[n] = cmat[rowidx, n]

      rowidx += 1

