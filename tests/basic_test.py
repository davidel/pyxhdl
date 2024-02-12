import argparse
import logging

import py_misc_utils.alog as alog
import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL


class Test(object):

  def __init__(self, x):
    self.xyz = x

  @X.hdl
  def func_one(self, p):
    return p + self.xyz

def free_func2(c, b):
  return c / b

def free_func1(o, p):
  return free_func2(o, p) + o - p

@X.hdl
def moo(x, y):
  return x * y + free_func1(x, y)

@X.hdl
def if_returns(x, y):
  if x > y:
    return x + y - 1
  else:
    return x - y + 1

@X.hdl
def zhdl(a, x=1):
  return a + 2 * x

@X.hdl
def rtuple(x, y):
  return x * y, x / y

@X.hdl
def test(a, b, q, d, f):
  if q >= 1:
    q = q + 1
    for i in range(4):
      logging.debug(i)

  if a > 0:
    c = a + b
    d = max(a, b) + moo(a, b)
    ifr = if_returns(q, q - 2)
    e = sum([a, b, d])
    l = lambda x, y: min(x, y)
    z = l(a, b)
    assert z > 0
    r = -q
    v = q + 2 - 2 * q - zhdl(q + a, x=q + 7)
    o = (q > 0) and (a > 0)
    r = -q
    z = max(a, b) - zhdl(q * a, x=2 - q)
  else:
    z = q / 7
    h = d - 2.1

  for i in range(a + 3):
    if i > 2:
      break
    for j in range(a + 1):
      logging.debug(f'j = {j}')
    q = q + 1

  i = 0
  while i < 10:
    q = q + q * b - 3
    if i > 3:
      break
    logging.debug(f'While i = {i}')
    i += 1
    l = [k + 1 for k in range(5, 20) if k > 10]
    dc = {f'{g}': g + 1 for g in range(2, 15) if g > 6}
    sc = {g * g for g in range(-2, 10) if g > 1}

  sz = 'ABC'
  ifexp = max(a, b) if a > b else b
  h_ifexp = q + 1 if q > 2 else q * 3

  if q > 5:
    if q < 12:
      q = q + 101
    if q == 3:
      q = q - 21

  logging.debug(type(q))
  logging.debug(isinstance(q, int))
  logging.debug(sz)

  ww = q[: 4] * 2 + q[4: ] * 7
  q[: 6] = 11

  a, q = 5, q

  nf = f + 1.0

  logging.debug(locals())


def _test_gen(args):
  emitter = X.Emitter.create(args.backend)
  codegen = X.CodeGen(emitter, X.create_globals(test, source_globals=globals()))

  with codegen.context():
    codegen.generate_process(
      test,
      [
        2,
        5,
        X.mkwire(X.UINT8, name='q'),
        1.7,
        X.mkreg(X.Float(4, 8, 32), name='f'),
      ],
      sensitivity=dict(
        a=X.Sens(),
        q=X.Sens(),
      ))

    logging.debug(f'CODE:')
    for ln in codegen.flush():
      print(ln)


class And(X.Entity):

  PORTS = (
    X.Port('a', X.IN),
    X.Port('b', X.IN),
    X.Port('c', X.OUT),
  )

  @X.hdl_process(
    sens=dict(
      a=X.Sens(),
      b=X.Sens(),
    ),
  )
  def run(a, b, c):
    c = a & b


class MyEntity(X.Entity):

  PORTS = (
    X.Port('a', X.IN),
    X.Port('b', X.IN),
    X.Port('c', X.OUT),
  )

  ARGS = dict(kwd='????')

  @X.hdl_process(
    kind=X.INIT_PROCESS
  )
  def init():
    e = X.mkwire(X.Uint(4))
    f = X.mkwire(X.Uint(4))

  @X.hdl_process(
    sens=dict(
      a=X.Sens(X.POSEDGE),
      b=X.Sens(),
    ),
  )
  def process_one():
    ar = X.mkreg(X.Uint(a.dtype.nbits))
    arr = XL.mkvreg(X.Uint(4, 4, 32), 0)
    if a > b:
      d = a
      j = 3
      arr[a + 1, j, 3: 17] = 0
    if a > c:
      d = c
      e = b[1: 5]
      f = e[1: 2]
      f = e[1: 4]
    ar = a + b

  @X.hdl_process(
    sens=dict(
      a=X.Sens(X.POSEDGE),
      c=X.Sens(),
    ),
  )
  def process_two():
    c = a + b
    ent1 = MyEntity(
      a=a,
      b=b,
      c=c,
      kwd='NEST_KWD',
    )
    c[2: 7] = 17

    aent = And(
      a=a,
      b=b,
      c=c,
    )

    d = a[2: 7]
    ent2 = MyEntity(
      a=a + b,
      b=d,
      c=c,
      kwd='NEST_KWD',
    )

    e = b[1: 5]

    z = Test(a)
    ww = z.func_one(17)

    c, n = rtuple(a, b + 165)

    XL.wait_rising(a, b)
    XL.wait_for(17)

    bx = X.mkwire(X.Bits(16))
    cx = X.mkwire(X.Bits(32))
    xx = bx[3: 14]
    xy = bx[13: 2: -1]
    if a:
      bx[: bx.dtype.nbits] = int('1001101', 2)
      cx = bx
      rr = a @ b
      assert a > 0, f'DANG! {kwd}'

      dd = dict()
      for v in range(8):
        dd[str(v)] = v + v / 2

      logging.debug(f'DD = {dd}')

      tt = Test(11)
      tt.qw = b
      bb = tt.qw - a

      ccc = XL.cast(a * b, rr.dtype)

    with XL.no_hdl():
      logging.debug(f'Look! No HDL! {cx}')

    after_no_hdl = 2 * ccc


def _test_entity(args):
  emitter = X.Emitter.create(args.backend)
  codegen = X.CodeGen(emitter, X.create_globals(MyEntity, source_globals=globals()))

  with codegen.context():
    codegen.generate_entity(MyEntity,
                            dict(a=X.mkwire(X.Uint(8)),
                                 b=X.mkwire(X.Uint(8)),
                                 c=X.mkwire(X.Uint(8)),
                                 kwd='KWD',
                                 ))


    logging.debug(f'CODE:')
    for ln in codegen.flush():
      print(ln)


def _main(args):
  _test_gen(args)
  _test_entity(args)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='PyXHDL Basic Tests',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--backend', type=str, default='VHDL',
                      choices=set(X.Emitter.available()),
                      help='The backend to generate the code for')

  alog.add_logging_options(parser)

  args = parser.parse_args()
  log.setup_logging(args)
  _main(args)

