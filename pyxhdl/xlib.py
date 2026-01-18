import py_misc_utils.inspect_utils as pyiu
import py_misc_utils.utils as pyu

from .decorators import *
from .emitter import *
from .pyxhdl import *
from .types import *
from .vars import *
from .utils import *
from .verilog_emitter import *
from .xcall import *


def comment(comm):
  ctx = CodeGen.current()

  return ctx.emitter.emit_comment(comm)


def register_module(mid, code, replace=None, global_reg=None):
  ctx = CodeGen.current()

  if global_reg is True or ctx is None:
    Emitter.glob_register_module(mid, code, replace=replace)
  else:
    ctx.emitter.register_module(mid, code, replace=replace)


def cast(value, dtype):
  ctx = CodeGen.current()

  return ctx.emitter.cast(value, dtype)


def load(name):
  ctx = CodeGen.current()

  return ctx.load_var(name)


def assign(name, value):
  ctx = CodeGen.current()

  ctx.assign_value(name, value)


def context(**kwargs):
  ctx = CodeGen.current()

  return ctx.emitter_context(**kwargs)


def no_hdl():
  ctx = CodeGen.current()

  return ctx.no_hdl()


def finish():
  ctx = CodeGen.current()
  ctx.emitter.emit_finish()


def wait_for(t=None):
  ctx = CodeGen.current()
  ctx.emitter.emit_wait_for(t=t)


def wait_rising(*args):
  ctx = CodeGen.current()
  ctx.emitter.emit_wait_rising(*args)


def wait_falling(*args):
  ctx = CodeGen.current()
  ctx.emitter.emit_wait_falling(*args)


def wait_until(*args):
  ctx = CodeGen.current()
  ctx.emitter.emit_wait_until(*args)


def report(fmt, **kwargs):
  ctx = CodeGen.current()
  ctx.emit_report(fmt, **kwargs)


def write(fmt, **kwargs):
  ctx = CodeGen.current()
  ctx.emit_write(fmt, **kwargs)


def xeval(code, **args):
  ctx = CodeGen.current()

  filename, lineno = pyiu.parent_coords()
  return ctx.run_code(code, args, 'eval', filename=filename, lineno=lineno)


def xexec(code, **args):
  ctx = CodeGen.current()

  filename, lineno = pyiu.parent_coords()
  ctx.run_code(code, args, 'exec', filename=filename, lineno=lineno)


## External Functions
float_equal = create_function(
  'float_equal',
  {
    'vhdl': 'pyxhdl.float_equal',
    'verilog': Verilog_Emitter.fpmod_resolve('fp_utils', 'rcloseto', 0),
  },
  fnsig='f*, real, real',
  dtype=BOOL)
