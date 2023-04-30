import logging
import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


_DUMMY_VHDL = """
context work.xlibs;

package dummy is
  function func(a : in unsigned; b : in unsigned) return unsigned;
  procedure proc(a : in unsigned; b : in unsigned);
end package;

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package body dummy is
  function func(a : in unsigned; b : in unsigned) return unsigned is
  begin
    return a + b;
  end function;

  procedure proc(a : in unsigned; b : in unsigned) is
  begin
    assert a > b report "Compare failed!" severity error;
  end procedure;
end package body;
"""

_DUMMY_VERILOG = """
package dummy;
  function automatic logic [7: 0] func;
    input logic [7: 0] a, b;
    begin
      func = a + b;
    end
  endfunction

  task proc;
    input logic [7: 0] a, b;
    begin
      assert (a > b) else $error("Compare failed!");
    end
  endtask
endpackage
"""

def _lazy_setup():
  global _dummy_proc, _dummy_func

  XL.register_module('dummy', {X.VHDL: _DUMMY_VHDL, X.VERILOG: _DUMMY_VERILOG})

  _dummy_proc = XL.create_function('dummy_proc',
                                   {
                                     X.VHDL: 'dummy.proc',
                                     X.VERILOG: 'dummy::proc',
                                   },
                                   fnsig='u*, u*')
  _dummy_func = XL.create_function('dummy_func',
                                   {
                                     X.VHDL: 'dummy.func',
                                     X.VERILOG: 'dummy::func',
                                   },
                                   fnsig='*, u8',
                                   dtype=XL.argn_dtype(0))


class XLib(X.Entity):

  PORTS = 'CLK, A, B, =XOUT'

  ARGS = dict(arg1=21, arg2='?')

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    _lazy_setup()

  @X.hdl_process(sens='CLK, A, B')
  def run():
    XL.report('TIME={NOW} A={A - B} B={A + B} arg1={arg1} arg2={arg2} $$vanilla')
    XL.write('TIME={NOW} A={A} B={B} arg1={arg1} arg2={arg2} $$vanilla')

    c = XL.xeval(f'A + B')
    XL.xexec(f'd = c * 2')

    _dummy_proc(c + B, A - d)

    e = X.mkreg(A.dtype)
    e = _dummy_func(A + 1, B * 3)

    XL.wait_until(A == 1)

    ctx = X.mkreg(A.dtype)
    with XL.context(delay=10):
      ctx = A * B

    z = X.mkreg(A.dtype)
    try:
      with XL.no_hdl():
        z = A + B
    except TypeError:
      XL.comment('Correctly erroring out while adding Value objects in non-HDL context')

    z = A * B
    assigned = X.mkreg(z.dtype)
    XL.assign('assigned', z - B)


class TestXLib(unittest.TestCase):

  def test_xlib(self):
    inputs = dict(
      CLK=X.mkwire(X.BIT),
      A=X.mkwire(X.UINT8),
      B=X.mkwire(X.UINT8),
      XOUT=X.mkwire(X.UINT8),

      arg1=17,
      arg2='PyXHDL',
    )

    tu.run(self, tu.test_name(self, pyu.fname()), XLib, inputs)

