# Cannot depend of local modules!
import numpy as np

import py_misc_utils.np_utils as pyn


class Wrapper:
  pass


class _NumpyWrapper(Wrapper):

  def __init__(self, value):
    super().__init__()
    self.value = value

  def __eq__(self, other):
    return self.value == other.value

  def __str__(self):
    return str(self.value.tolist())

  def __hash__(self):
    return pyn.hasher(self.value)


def unwrap(value):
  if isinstance(value, Wrapper):
    return value.value

  # Numpy scalars expose themselves as Python 'float, int' but are rejected by compile()
  # as they show up as 'np.float*, np.int*'.
  if isinstance(value, np.number):
    return value.item()

  return value


def wrap(value):
  if isinstance(value, np.ndarray):
    return _NumpyWrapper(value)

  return value

