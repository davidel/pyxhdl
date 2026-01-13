import ast
import copy

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

  class Transformer(ast.NodeTransformer):

    def visit_Store(self, node):
      return ast.Load()


  cnode = node if inplace else copy.deepcopy(node)

  return Transformer().visit(cnode)

