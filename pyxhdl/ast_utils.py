import ast
import copy
import os

import py_misc_utils.ast_utils as asu

from .utils import *


def ast_hdl_transform(node):
  asu.ifize(node)

  return node


def elements(c):
  if isinstance(c, (list, tuple)):
    return c
  if isinstance(c, (ast.List, ast.Tuple)):
    return c.elts


def as_loading(node, inplace=False):
  cnode = node if inplace else copy.deepcopy(node)

  def trans_fn(node):
    return ast.Load() if isinstance(node, ast.Store) else node

  return asu.Tranformer(trans_fn).visit(cnode)

