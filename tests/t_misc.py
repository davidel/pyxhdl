import logging
import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


@X.hdl
def tuple_fn(x, y):
  return x + y, x - y


@X.hdl
def dict_fn(x, y):
  d = dict()
  d['q'] = x * y - 1
  d['w'] = x + y * 3

  return d


@X.hdl
def branchy(a, b):
  if a > b:
    return a + b

  return a - b


@X.hdl
def compose(a, b):
  return branchy(a, b) + a


@X.hdl
def branchy_tuple(a, b):
  if a > b:
    return a + b, a

  return a - b, a + b


@X.hdl
def compose_tuple(a, b):
  return branchy_tuple(a, b)


@X.hdl
def branchy_dict(a, b):
  if a > b:
    return dict(X=a + b, Y=a)

  return dict(X=a - b, Y=a + b)


@X.hdl
def twice_locals(a, b):
  twicer = a + b

  return a - b + twicer


@X.hdl
def twice_decl(a, b):
  twdecl = X.mkwire(b.dtype)
  twdecl = a + b

  return a - b + twdecl


class Misc(X.Entity):

  PORTS = 'A, B, C, +XOUT1, +XOUT2'

  @X.hdl_process(sens='A, B, C')
  def run():
    na = nb = br = X.mkwire(A.dtype)
    nb, na = tuple_fn(A, B)

    dv = dict_fn(na, nb)
    dr = dv['q'] - dv['w']

    sb = XL.cast(na[2], X.BIT)
    if sb == '0bX':
      na = na + nb
    elif sb == '0bU':
      na = na - nb

    # This is broken ATM because of RETURN handling within HDL dependent IF
    # statements.
    br = branchy(A, B)
    comp = compose(A, B)

    tbr0, tbr1 = branchy_tuple(A, B)
    comp0, comp1 = compose_tuple(A, B)

    zz = X.mkwire(A.dtype)
    brd = branchy_dict(tbr0, tbr1)
    zz = brd['X'] * brd['Y']

    if C == '0b0110X110':
      bits = C @ '0b11001'

    rbits = XL.mkvwire(C.dtype, '0b1101X0X0')
    if C != rbits:
      sbits = '0b1XX0' @ C
    if A == 'u8`127':
      zz = A * B

    tw1 = tw2 = X.mkwire(A.dtype)
    tw1 = twice_locals(A, B)
    tw2 = twice_locals(A, B)

    twd1 = twd2 = X.mkwire(A.dtype)
    twd1 = twice_decl(A, B)
    twd2 = twice_decl(A, B)

    XOUT1 = A - B - dr + zz

  @X.hdl_process(sens='A, B, C')
  def use_self(self):
    XOUT2 = A - B + XL.cast(C, XOUT2.dtype) + len(self.args)


class TestMisc(unittest.TestCase):

  def test_misc_8_8(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      C=X.mkwire(X.Bits(8)),
      XOUT1=X.mkreg(X.UINT8),
      XOUT2=X.mkreg(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), Misc, inputs)

  def test_misc_8_4(self):
    inputs = dict(
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.Uint(4)),
      C=X.mkwire(X.Bits(8)),
      XOUT1=X.mkreg(X.UINT8),
      XOUT2=X.mkreg(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), Misc, inputs)

