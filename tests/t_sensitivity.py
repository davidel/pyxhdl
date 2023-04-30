import logging
import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class PosEdge(X.Entity):

  PORTS = (
    X.Port('CLK', X.IN),
    X.Port('RESET', X.IN),
    X.Port('XOUT', X.OUT),
  )

  @X.hdl_process(
    sens=dict(
      CLK=X.Sens(X.POSEDGE),
      RESET=X.Sens(),
    ),
  )
  def run():
    if RESET != 0:
      XOUT = 0


class NegEdge(X.Entity):

  PORTS = (
    X.Port('CLK', X.IN),
    X.Port('RESET', X.IN),
    X.Port('XOUT', X.OUT),
  )

  @X.hdl_process(
    sens=dict(
      CLK=X.Sens(X.NEGEDGE),
      RESET=X.Sens(),
    ),
  )
  def run():
    if RESET != 0:
      XOUT = 0


class EdgeString(X.Entity):

  PORTS = (
    X.Port('CLK', X.IN),
    X.Port('RESET', X.IN),
    X.Port('XOUT', X.OUT),
  )

  @X.hdl_process(sens='+CLK, RESET')
  def run():
    if RESET != 0:
      XOUT = 0


class TestSensitivity(unittest.TestCase):

  def test_posedge(self):
    inputs = dict(
      CLK=X.mkwire(X.BIT),
      RESET=X.mkwire(X.BIT),
      XOUT=X.mkwire(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), PosEdge, inputs)

  def test_negedge(self):
    inputs = dict(
      CLK=X.mkwire(X.BIT),
      RESET=X.mkwire(X.BIT),
      XOUT=X.mkwire(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), NegEdge, inputs)

  def test_edge_string(self):
    inputs = dict(
      CLK=X.mkwire(X.BIT),
      RESET=X.mkwire(X.BIT),
      XOUT=X.mkwire(X.UINT8),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), EdgeString, inputs)

