import collections
import difflib
import inspect
import logging
import os
import sys
import unittest

import py_misc_utils.core_utils as pycu

import pyxhdl as X
from pyxhdl import xlib as XL


_BACKEND_ARGS = collections.defaultdict(dict)


def add_backend_arg(backend, name, value):
  bdict = _BACKEND_ARGS[backend]
  pycu.dict_add(bdict, name, value)


def test_name(obj, name):
  func = getattr(obj, name)
  cls, name = func.__func__.__qualname__.split('.', 1)

  return f'{cls}__{name}'


def is_regen_mode():
  mode = os.environ.get('REGEN_TESTS')

  return mode is not None and int(mode) != 0


def data_folder():
  return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


_BACKEND_EXTS = {
  X.VHDL: '.vhd',
  X.VERILOG: '.sv',
}

def reference_path(name, backend, path=None):
  ext = _BACKEND_EXTS.get(backend, f'.{backend}')

  return os.path.join(path or data_folder(), f'{name}{ext}')


def load_reference(name, backend):
  path = reference_path(name, backend)
  if os.path.exists(path):
    with open(path, mode='r') as rfd:
      return rfd.read().split('\n')[: -1]


def store_reference(name, backend, code):
  path = reference_path(name, backend, path=os.environ.get('DEST_PATH'))
  logging.info(f'Storing reference code: name={name} banckend={backend} path={path}')
  with open(path, mode='w') as rfd:
    for cln in code:
      rfd.write(cln + '\n')


def generate_code(obj, inputs, backend):
  eargs = _BACKEND_ARGS[backend]
  emitter = X.Emitter.create(backend, **eargs)

  gglobals = X.create_globals(obj)
  codegen = X.CodeGen(emitter, gglobals)

  with codegen.context():
    if inspect.isclass(obj):
      codegen.generate_entity(obj, inputs)
    else:
      codegen.generate_process(obj, inputs)

    return codegen.flush()


def _run_test(test_obj, name, obj, inputs, backend):
  code = generate_code(obj, inputs, backend)

  ref_code = load_reference(name, backend)
  if ref_code is None:
    if is_regen_mode():
      store_reference(name, backend, code)
    else:
      test_obj.skipTest(f'Reference code not available for {backend} test: {name}')
  else:
    diff = difflib.unified_diff(ref_code, code,
                                fromfile=f'old_{name}',
                                tofile=f'new_{name}',
                                lineterm='')

    lines = list(diff)
    if lines:
      if is_regen_mode():
        store_reference(name, backend, code)
      else:
        txt_diff = '\n'.join(lines)
        test_obj.fail('\n' + txt_diff)


def run(test_obj, name, obj, inputs):
  for backend in X.Emitter.available():
    _run_test(test_obj, name, obj, inputs, backend)

