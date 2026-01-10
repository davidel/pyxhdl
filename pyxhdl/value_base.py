import ast
import logging

import py_misc_utils.run_once as pyro
import py_misc_utils.utils as pyu


# Avoid dependency cycles ...
@pyro.run_once
def _lazy_import():
  global X

  import pyxhdl as X


# This is the Value's base class and implements a Python data model for the Value class.
# NOTE: This interface gets only used when performing Value instances operations outside
# of the HDL marked scope (the @X.hdl or @X.hdl_process(...) decorators).
# Note also that although it is possible to perform certain operations of Value while outside
# of the HDL scopes, a few things do not work.
# It is not possible to use Python IF statements depending on Value instances, as well as it
# is not possible to compose logical operations on them (like, "a > b and e < f" - only
# possible using the ValueBase And(), Or() and Not() functions, like "(a > b).And(e < f)").
# To handle those cases, PyXHDL has to interpret the AST tree and emit the matching
# HDL code, which happens while within an HDL scope.
# IOW, HDL variables (Value instances) processing should happen within HDL scopes, and
# the datamodel interface is only provided as fallback.
class ValueBase:

  def __init__(self):
    _lazy_import()

  @staticmethod
  def load(name):
    _lazy_import()

    ctx = X.CodeGen.current()

    return ctx.load_var(name)

  def store(self, name):
    ctx = X.CodeGen.current()

    ctx.assign_value(name, self)

  # Conversions
  def cast(self, dtype):
    ctx = X.CodeGen.current()

    return ctx.emitter.cast(self, dtype)

  # Arithmetic
  def __add__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.Add(), self, other)

  def __sub__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.Sub(), self, other)

  def __mul__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.Mult(), self, other)

  def __truediv__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.Div(), self, other)

  def __mod__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.Mod(), self, other)

  def __lshift__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.LShift(), self, other)

  def __rshift__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.RShift(), self, other)

  def __and__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.BitAnd(), self, other)

  def __or__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.BitOr(), self, other)

  def __xor__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.BitXor(), self, other)

  def __matmul__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.MatMult(), self, other)

  # Unaries
  def __neg__(self):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_UnaryOp(ast.USub(), self)

  def __pos__(self):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_UnaryOp(ast.UAdd(), self)

  def __invert__(self):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_UnaryOp(ast.Invert(), self)

  # Compare
  def __eq__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_Compare(self, [ast.Eq()], [other])

  def __ne__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_Compare(self, [ast.NotEq()], [other])

  def __lt__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_Compare(self, [ast.Lt()], [other])

  def __le__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_Compare(self, [ast.LtE()], [other])

  def __gt__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_Compare(self, [ast.Gt()], [other])

  def __ge__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_Compare(self, [ast.GtE()], [other])

  # The *R* versions
  def __radd__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.Add(), other, self)

  def __rsub__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.Sub(), other, self)

  def __rmul__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.Mult(), other, self)

  def __rtruediv__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.Div(), other, self)

  def __rmod__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.Mod(), other, self)

  def __rlshift__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.LShift(), other, self)

  def __rrshift__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.RShift(), other, self)

  def __rand__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.BitAnd(), other, self)

  def __ror__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.BitOr(), other, self)

  def __rxor__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.BitXor(), other, self)

  def __rmatmul__(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BinOp(ast.MatMult(), other, self)

  # Arithmetic Self Assign
  def _ires(self, res):
    self.__dict__.update(res.__dict__)

    return self

  def __iadd__(self, other):
    ctx = X.CodeGen.current()

    return self._ires(ctx.emitter.eval_BinOp(ast.Add(), self, other))

  def __isub__(self, other):
    ctx = X.CodeGen.current()

    return self._ires(ctx.emitter.eval_BinOp(ast.Sub(), self, other))

  def __imul__(self, other):
    ctx = X.CodeGen.current()

    return self._ires(ctx.emitter.eval_BinOp(ast.Mult(), self, other))

  def __itruediv__(self, other):
    ctx = X.CodeGen.current()

    return self._ires(ctx.emitter.eval_BinOp(ast.Div(), self, other))

  def __imod__(self, other):
    ctx = X.CodeGen.current()

    return self._ires(ctx.emitter.eval_BinOp(ast.Mod(), self, other))

  def __ilshift__(self, other):
    ctx = X.CodeGen.current()

    return self._ires(ctx.emitter.eval_BinOp(ast.LShift(), self, other))

  def __irshift__(self, other):
    ctx = X.CodeGen.current()

    return self._ires(ctx.emitter.eval_BinOp(ast.RShift(), self, other))

  def __iand__(self, other):
    ctx = X.CodeGen.current()

    return self._ires(ctx.emitter.eval_BinOp(ast.BitAnd(), self, other))

  def __ior__(self, other):
    ctx = X.CodeGen.current()

    return self._ires(ctx.emitter.eval_BinOp(ast.BitOr(), self, other))

  def __ixor__(self, other):
    ctx = X.CodeGen.current()

    return self._ires(ctx.emitter.eval_BinOp(ast.BitXor(), self, other))

  # Item operations
  def __getitem__(self, idx):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_Subscript(self, idx)

  # Logical **functions** (note that it is not possible to override the Python
  # logical AND, OR and NOT at the datamodel level).
  def And(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BoolOp(ast.And(), (self, other))

  def Or(self, other):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_BoolOp(ast.Or(), (self, other))

  def Not(self):
    ctx = X.CodeGen.current()

    return ctx.emitter.eval_UnaryOp(ast.Not(), self)

  # Allow for Value functions to map directly to emitter eval_*() ones.
  def __getattr__(self, attr):
    ctx = X.CodeGen.current()
    emitter_fn = getattr(ctx.emitter, f'eval_{attr}', None)
    if emitter_fn is None:
      raise AttributeError(f'Not implemented: {attr}')

    def fncall(*args, **kwargs):
      return emitter_fn(self, *args, **kwargs)

    return fncall

