# TestBench data generator for the trivial MatMul unit.
import argparse

import numpy as np

import py_misc_utils.alog as alog
import py_misc_utils.app_main as app_main
import py_misc_utils.gfs as gfs
import py_misc_utils.obj as obj
import py_misc_utils.rnd_utils as pyr
import py_misc_utils.utils as pyu

import pyxhdl as X
import pyxhdl.main_utils as XM


_MFIELDS = ('AROW', 'BROW', 'CROW')


def _genmat(size, dtype, scaler):
  mat = np.random.rand(size, size)
  if np.issubdtype(dtype, np.integer):
    mat = mat * scaler

  return mat.astype(dtype)


def _main(args):
  pyr.manual_seed(args.seed)

  dtype = np.dtype(args.dtype)

  mdata = []
  for n in range(args.nsamples):
    gs = obj.Obj()
    gs._wait_expr = 'XL.wait_rising(CLK)'
    mdata.append(gs)

    gs = obj.Obj()
    gs.RESET = 1
    gs._wait_expr = 'XL.wait_rising(CLK)'
    mdata.append(gs)

    gs = obj.Obj()
    gs.RESET = 0
    gs._wait_expr = 'XL.wait_rising(CLK)'
    mdata.append(gs)

    amat = _genmat(args.dimsize, dtype, args.scaler)
    bmat = _genmat(args.dimsize, dtype, args.scaler)
    cmat = amat @ bmat

    for i in range(args.dimsize):
      gs = obj.Obj()
      gs.INFEED = 1
      gs.AROW = amat[i].tolist()
      gs.BROW = bmat[i].tolist()
      gs._wait_expr = 'XL.wait_rising(CLK)'
      mdata.append(gs)

    gs = obj.Obj()
    gs.INFEED = 0
    gs.COMPUTE = 1
    gs._wait_expr = 'XL.wait_rising(CLK)'
    mdata.append(gs)

    gs = obj.Obj()
    gs.COMPUTE = 0
    gs._wait_expr = 'XL.wait_rising(CLK)'
    mdata.append(gs)

    gs = obj.Obj()
    gs._wait_expr = 'XL.wait_until(READY == 1)'
    mdata.append(gs)

    gs = obj.Obj()
    gs.OUTFEED = 1
    gs._wait_expr = 'XL.wait_rising(CLK)'
    mdata.append(gs)

    for i in range(args.dimsize):
      gs = obj.Obj()
      gs.OUTFEED = 1 if i + 1 < args.dimsize else 0
      gs.CROW = cmat[i].tolist()
      gs._wait_expr = 'XL.wait_rising(CLK)'
      mdata.append(gs)


  data = obj.Obj()
  data.conf = obj.Obj(loaders={fn: dict(kind='numpy', dtype=args.dtype) for fn in _MFIELDS})
  data.data = mdata

  with gfs.std_open(args.output_file, mode='w') as ofd:
    ofd.write(pyu.config_to_string(data.as_dict()))


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='MatMult TestBench Data Generator',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--dimsize', type=int, default=128,
                      help='The size of the matrices to be multiplied')
  parser.add_argument('--dtype', type=str, default='float32',
                      help='The data type')
  parser.add_argument('--scaler', type=int, default=32,
                      help='Scaler for integer input matrix')
  parser.add_argument('--nsamples', type=int, default=4,
                      help='How many test cases to be generated')
  parser.add_argument('--output_file', type=str, default='STDOUT',
                      help='The path to the output file for the generated data (default STDOUT)')
  parser.add_argument('--seed', type=int,
                      help='The random number generator seed')

  app_main.main(parser, _main)

