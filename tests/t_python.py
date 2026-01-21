import math
import unittest

import numpy as np

import py_misc_utils.alog as alog
import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

import test_utils as tu


class _FakeCtx(object):

  def __init__(self, v):
    self.v = v

  def __enter__(self):
    return self

  def __exit__(self, xtype, ex, tb):
    alog.debug(f'FAKE CTX: {xtype}\t{ex}\t{tb}')
    return True


def _fake_ctx(v):
  return _FakeCtx(v)


def _args_call(*args):
  return args


@X.hdl
def yield_fn(l):
  for x in l:
    yield x


@X.hdl
def yield_from_fn(l):
  yield from l


@X.hdl
def none_return():
  return


class PythonEnt(X.Entity):

  PORTS = (
    X.Port('DUMMY_A', X.Port.IN),
    X.Port('DUMMY_OUT', X.Port.OUT),
  )

  ARGS = dict(i=0, j=0, f=0.0, s='', l=[], d=dict())

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def run():
    XL.comment(f'i = {i}')
    XL.comment(f'j = {j}')
    XL.comment(f'f = {f}')
    XL.comment(f's = {s}')
    XL.comment(f'l = {l}')
    XL.comment(f'd = {d}')

    dd = {n: f'{n + 1}' for n in range(i + 5, i + 10)}
    XL.comment(f'dd = {dd}')

    ll = [f'{round(f + i - j) + n}' for n in range(-2, j - 5)]
    XL.comment(f'll = {ll}')

    fd = dict()
    for n in range(min(i, j) - 5):
      fd[n] = f'{s} {n}'
    XL.comment(f'fd = {fd}')

    bigs = f'{s[: -1]} ' * (min(i, j) - 10)
    XL.comment(f'bigs = {bigs}')

    a = np.arange(min(i, j), max(i, j))
    XL.comment(f'a = {a.shape}\n{a}')

    ra = np.arange(0, 16).reshape(4, 4)
    XL.comment(f'ra = {ra.shape}\n{ra}')

    ras = ra[1, ...]
    XL.comment(f'ras = {ras.shape}\n{ras}')

    rax = ra[0: 2, 1: 3]
    XL.comment(f'rax = {rax.shape}\n{rax}')

    npt = np.array([2.3, 3.4, 4.5])
    npr = npt * 3.2 - npt
    XL.comment(f'npr = {npr.shape}\n{npr}')

    l = lambda x, y: max(x, y)
    XL.comment(f'lres = {l(i, j)}')

    XL.comment(f'tll = {tuple(ll)}')

    XL.comment(f'sinf = {math.sin(f):.4f}')

    XL.comment(f'xlog = {math.exp(math.log(f)):.4f}')

    try:
      raise RuntimeError(f'CatchMe {d}')
    except Exception as e:
      XL.comment(f'except = {e}')

    try:
      pp = np.prod([i, j, f])
    except:
      pass
    else:
      XL.comment(f'else pp = {pp:.3f}')
    finally:
      XL.comment(f'finally fd = {fd}')

    global GVAR
    GVAR = i - j + math.log(10 * f)
    XL.comment(f'gvar = {"GVAR" in globals()}, {GVAR:.4f}')

    na = np.array([isinstance(DUMMY_A, X.Wire), isinstance(DUMMY_OUT, X.Wire)])
    XL.comment(f'na = {na.shape}\n{na}')

    xss = {1, 2, 'XYZ'}
    XL.comment(f'xss = {sorted(xss, key=lambda x: str(x))}')

    xdd = {1: 101, 'A': -1.2, 3.11: True}
    XL.comment(f'xdd = {xdd}')

    with _fake_ctx(21) as fc:
      XL.comment(f'fctx = {fc.v}')

    XL.comment(f'nret = {none_return()}')

    for x in yield_fn((4, 5, 6)):
      XL.comment(f'yield_fn = {x}')

    for x in yield_from_fn((17, 21, 33)):
      XL.comment(f'yield_from_fn = {x}')

    cargs = (1, 3.14, 'XYZ')
    XL.comment(f'cargs = {_args_call(*cargs)}')


class TestPython(unittest.TestCase):

  def test_python(self):
    inputs = dict(
      # Unused, to avoid warnings about empty interfaces.
      DUMMY_A=X.mkwire(X.UINT8),
      DUMMY_OUT=X.mkwire(X.UINT8),
      # Used vars below ...
      i=17,
      j=21,
      f=3.14,
      s='ABC',
      l=[1, 2, 3],
      d=dict(a=3, b=11, c=65),
    )

    tu.run(self, tu.test_name(self, pyu.fname()), PythonEnt, inputs)

