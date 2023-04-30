import argparse
import logging
import os
import unittest

import py_misc_utils.utils as pyu

import pyxhdl as X


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='PyXHDL Tests Runner',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--verbosity', type=int, default=2,
                      help='The test verbosity')
  parser.add_argument('--files', type=str, default='t_*.py',
                      help='The pattern to match files whose tests need to be run')
  parser.add_argument('--log_level', type=str, default='INFO',
                      choices={'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'},
                      help='The logging level')
  parser.add_argument('--log_file', type=str,
                      help='The log file path')

  args = parser.parse_args()
  pyu.setup_logging(log_level=args.log_level, log_file=args.log_file)

  test_folder = os.path.dirname(os.path.abspath(__file__))

  loader = unittest.TestLoader()
  tests = loader.discover(test_folder, pattern=args.files)
  runner = unittest.runner.TextTestRunner(verbosity=args.verbosity)
  runner.run(tests)

