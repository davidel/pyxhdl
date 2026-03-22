import ast
import copy

import py_misc_utils.ast_utils as asu

from .utils import *


def ast_hdl_transform(node, inplace=False):
  tnode = node if inplace else copy.deepcopy(node)

  asu.ifize(tnode)

  return tnode


def elements(c):
  if isinstance(c, (list, tuple)):
    return c
  if isinstance(c, (ast.List, ast.Tuple)):
    return c.elts


def as_loading(node, inplace=False):

  class Transformer(ast.NodeTransformer):

    def visit_Store(self, node):
      return ast.Load()


  tnode = node if inplace else copy.deepcopy(node)

  return Transformer().visit(tnode)

