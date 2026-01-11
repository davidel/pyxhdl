import argparse
import os
import unittest

import py_misc_utils.app_main as app_main
import py_misc_utils.utils as pyu

import pyxhdl as X


def _main(args):
  test_folder = os.path.dirname(os.path.abspath(__file__))

  loader = unittest.TestLoader()
  tests = loader.discover(test_folder, pattern=args.files)
  runner = unittest.runner.TextTestRunner(verbosity=args.verbosity)
  runner.run(tests)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='PyXHDL Tests Runner',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--verbosity', type=int, default=2,
                      help='The test verbosity')
  parser.add_argument('--files', type=str, default='t_*.py',
                      help='The pattern to match files whose tests need to be run')

  app_main.main(parser, _main)

