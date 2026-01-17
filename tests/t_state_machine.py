import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class States:
  IDLE = 0
  WAIT = 1
  START = 2
  VALUES = 3
  STOP = 4

  MAX = STOP


class StateMachine(X.Entity):

  PORTS = 'CLK, RST_N, BITLINE, =RDEN, =RDATA'

  @X.hdl_process(sens='+CLK')
  def state_machine(self):
    state = X.mkvreg(X.Uint(States.MAX.bit_length()), 0)
    count = X.mkvreg(X.Uint(RDATA.dtype.nbits.bit_length()), 0)
    value = X.mkreg(RDATA.dtype)

    if not RST_N:
      state = States.IDLE
      count = 0
      RDEN = 0
      RDATA = '0bX'
    else:
      match state:
        case States.IDLE:
          if BITLINE == 1:
            state = States.WAIT

        case States.WAIT:
          if BITLINE == 0:
            state = States.START
            count = 0
            value = 0
            RDEN = 0

        case States.START:
          value = (value << 1) | BITLINE
          if count == RDATA.dtype.nbits - 1:
            state = States.STOP
          else:
            count += 1

        case States.STOP:
          if BITLINE == 0:
            RDEN = 1
            RDATA = value

          state = States.IDLE
        case _:
          pass


class TestStateMachine(unittest.TestCase):

  def test_state_machine(self):
    inputs = dict(
      CLK=X.mkwire(X.BIT),
      RST_N=X.mkwire(X.BIT),
      BITLINE=X.mkwire(X.BIT),
      RDEN=X.mkreg(X.BIT),
      RDATA=X.mkreg(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), StateMachine, inputs)

