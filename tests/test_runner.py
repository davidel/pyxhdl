import argparse
import os
import re
import unittest

import py_misc_utils.alog as alog
import py_misc_utils.app_main as app_main
import py_misc_utils.core_utils as pycu
import py_misc_utils.utils as pyu

import pyxhdl as X

import test_utils as tu


def _main(args):
  test_folder = (args.test_folder or
                 os.environ.get('TESTS_FOLDER') or
                 os.path.dirname(os.path.abspath(__file__)))

  alog.debug(f'TestFolder: {test_folder}')

  for arg in args.backed_arg or ():
    m = re.match(r'([^\s]+)\s*:\s*([^\s]+)(\s*=\s*([^\s]+))?', arg)
    if not m:
      pyu.fatal(f'Invalid backend argument: {arg}')

    value = pycu.infer_value(m.group(4)) if m.group(4) else None
    tu.add_backend_arg(m.group(1), m.group(2), value)

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
  parser.add_argument('--test_folder',
                      help='The folder where the test files are stored')
  parser.add_argument('--backed_arg', nargs='*',
                      help='An argument for the backend (ie, "VHDL:VAR=VALUE")')

  app_main.main(parser, _main)

