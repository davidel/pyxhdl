# Cannot depend of local modules!
import logging

import numpy as np


class Wrapper(object):
  pass


class _NumpyWrapper(Wrapper):

  def __init__(self, value):
    super().__init__()
    self._value = value

  @property
  def value(self):
    return self._value

  def __eq__(self, other):
    return self._value == other._value

  def __str__(self):
    return str(self._value.tolist())

  def __hash__(self):
    return hash((str(self._value.dtype), tuple(self._value.shape), self._value.tobytes()))



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

