import ast
import collections
import copy
import inspect
import logging
import re
import textwrap

import py_misc_utils.ast_utils as asu
import py_misc_utils.context_managers as pycm
import py_misc_utils.core_utils as pycu
import py_misc_utils.inspect_utils as pyiu
import py_misc_utils.utils as pyu

from .ast_utils import *
from .decorators import *
from .entity import *
from .types import *
from .vars import *
from .utils import *
from .wrap import *


ROOT_PROCESS = '$ROOT'
INIT_PROCESS = '$INIT'

_Variable = collections.namedtuple('Variable', 'dtype, isreg, init, vspec', defaults=[None, None])
_Return = collections.namedtuple('Return', 'value, placement')
_MatchCase = collections.namedtuple('MatchCase', 'pattern, scope')

_CGENCTX = 'pyxhdl.CodeGen'
_CODEFMT_RX = r'(?<!\{)\{([^{][^}]*(\}\}[^}]+)*)\}'
_NONE = object()


class _Exception(Exception):
  pass


class _ReturnException(_Exception):

  def __init__(self, value):
    super().__init__()
    self.value = value


class _BreakException(_Exception):
  pass


class _ContinueException(_Exception):
  pass


class _SourceLocation(object):

  def __init__(self, filename, base_lineno):
    self.filename = filename
    self.base_lineno = base_lineno
    self.lineno = base_lineno

  def set_lineno(self, lineno):
    self.lineno = self.base_lineno + lineno - 1


class _Storer(object):
  pass


class _StoreAttribute(_Storer):

  def __init__(self, target, attr):
    super().__init__()
    self.target = target
    self.attr = attr

  def store(self, value):
    setattr(self.target, self.attr, value)


class _StoreSubscript(_Storer):

  def __init__(self, target, index):
    super().__init__()
    self.target = target
    self.index = index

  def store(self, value):
    self.target[self.index] = value


class _AstVisitor(ast.NodeVisitor):

  def __init__(self):
    super().__init__()
    self._default_visitor = getattr(self, 'visit_default', self.generic_visit)
    self._catchall_visitors = []

  def add_catchall(self, visitor):
    self._catchall_visitors.append(visitor)

  def pop_catchall(self):
    self._catchall_visitors.pop()

  def visit(self, node):
    if self._catchall_visitors:
      visitor = self._catchall_visitors[-1]
    else:
      method = 'visit_' + pyu.cname(node)
      visitor = getattr(self, method, self._default_visitor)

    return visitor(node)


class _Frame(object):

  def __init__(self, fglobals, flocals, location):
    self.fglobals = fglobals
    self.flocals = flocals
    self.location = location
    self.yields = []
    self.global_names = set()
    self.in_hdl_branch = 0
    self.return_values = []
    self.retval = None

  def new_locals(self, flocals):
    return pyu.new_with(self, flocals=flocals)


class _ExecVisitor(_AstVisitor):

  def __init__(self, vglobals, vlocals=None):
    super().__init__()
    self._frames = [_Frame(vglobals, vlocals or dict(), _SourceLocation('NOFILE', 0))]
    self._variables = []
    self._results = []
    self._revgen = pyu.RevGen()

  @property
  def frame(self):
    return self._frames[-1]

  @property
  def locals(self):
    return self.frame.flocals

  @property
  def globals(self):
    return self.frame.fglobals

  @property
  def global_names(self):
    return self.frame.global_names

  @property
  def location(self):
    return self.frame.location

  @property
  def yields(self):
    return self.frame.yields

  @property
  def variables(self):
    return self._variables[-1]

  @property
  def results(self):
    return self._results[-1] if self._results else None

  def _frame(self, frame):
    def infn():
      self._frames.append(frame)
      return self

    def outfn(*exc):
      self._frames.pop()
      return False

    return pycm.CtxManager(infn, outfn)

  def _hdl_branch(self):
    frame = self.frame

    def infn():
      frame.in_hdl_branch += 1
      return self

    def outfn(*exc):
      frame.in_hdl_branch -= 1
      return False

    return pycm.CtxManager(infn, outfn)

  def _exec_locals(self, tmp_values):
    # Override temporary values, but keep the changes to the locals.
    save_dict = dict()

    def infn():
      ref_dict = self.locals
      for k, v in tmp_values.items():
        save_dict[k] = ref_dict.get(k, _NONE)
        ref_dict[k] = v

      return self

    def outfn(*exc):
      ref_dict = self.locals
      for k, v in save_dict.items():
        if v is _NONE:
          ref_dict.pop(k)
        else:
          ref_dict[k] = v

      return False

    return pycm.CtxManager(infn, outfn)

  def _eval_locals(self, tmp_values):
    # Apply temporary changes during the eval operation, but revert to previous
    # status afterwards (do not persist eventual changes).
    save_dict = self.locals.copy()

    def infn():
      ref_dict = self.locals
      for k, v in tmp_values.items():
        ref_dict[k] = v

      return self

    def outfn(*exc):
      self.locals.clear()
      self.locals.update(save_dict)

      return False

    return pycm.CtxManager(infn, outfn)

  def _store_value(self, name, value):
    if name in self.global_names:
      self.globals[name] = value
    else:
      self.locals[name] = value

  def _add_variable(self, name, dtype, isreg, init=None, vspec=None):
    pyu.mlog(lambda: f'NEW VAR: {valkind(isreg)} {dtype}\t{name}')

    self.variables[name] = _Variable(dtype=dtype, isreg=isreg, init=init, vspec=vspec)

  def _static_eval(self, node):
    self.location.set_lineno(node.lineno)

    return asu.static_eval(node, self.globals, self.locals, filename=self.location.filename)

  def _eval_node(self, node, visit_node=True):
    self.location.set_lineno(node.lineno)

    results = []
    self._results.append(results)
    try:
      if visit_node:
        self.visit(node)
      else:
        pyu.mlog(lambda: asu.dump(node))
        self.generic_visit(node)
    finally:
      self._results.pop()

    return results[0] if len(results) == 1 else results if results else None

  def _annotated_exception(self, ex):
    noted = getattr(ex, '_noted', False)
    if not noted:
      # Discard the 0-th entry as it is the NOFILE dummy one.
      locs = []
      for f in self._frames[1: ]:
        locs.append(f'{f.location.filename}:{f.location.lineno}')

      xmsg = f'{ex}\nError stack:\n' + '\n'.join(locs)
      ex = ex.__class__(xmsg).with_traceback(ex.__traceback__)
      setattr(ex, '_noted', True)

    return ex

  def eval_node(self, node, visit_node=True):
    try:
      return self._eval_node(node, visit_node=visit_node)
    except _Exception:
      # These are internal exceptions meant to be left as is.
      raise
    except Exception as ex:
      raise self._annotated_exception(ex)

  def push_result(self, result):
    results = self.results
    if results is not None:
      results.append(result)

  def push_yield(self, value):
    yields = self.yields
    if yields is not None:
      yields.append(value)

  def _get_function_body(self, name, node):
    if isinstance(node, ast.Module):
      for mnode in node.body:
        if isinstance(mnode, ast.FunctionDef) and mnode.name == name:
          return mnode.body

    logging.warning(f'Function "{name}" body not found in node: {asu.dump(node)}')

    return [node]

  def _populate_args_locals(self, sig, args, kwargs, func_locals):
    xkwargs = kwargs.copy()
    n = 0
    for param in sig.parameters.values():
      if param.kind == inspect.Parameter.POSITIONAL_ONLY:
        func_locals[param.name] = args[n]
        n += 1
      elif param.kind == inspect.Parameter.VAR_POSITIONAL:
        func_locals[param.name] = args[n: ]
        n = len(args)
      elif param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
        pvalue = xkwargs.pop(param.name, _NONE)
        if pvalue is not _NONE:
          func_locals[param.name] = pvalue
        else:
          func_locals[param.name] = args[n]
          n += 1
      elif param.kind == inspect.Parameter.KEYWORD_ONLY:
        pvalue = xkwargs.pop(param.name, _NONE)
        if pvalue is _NONE and param.default != inspect.Parameter.empty:
          pvalue = param.default
        func_locals[param.name] = pvalue
      elif param.kind == inspect.Parameter.VAR_KEYWORD:
        func_locals[param.name] = xkwargs
        xkwargs = dict()

    return xkwargs

  def _generate_retval_result(self, fname, value, vindex, tmp_names):
    if isinstance(value, (list, tuple)):
      results = []
      for lvalue in value:
        rvalue, vindex = self._generate_retval_result(fname, lvalue, vindex, tmp_names)
        results.append(rvalue)

      return type(value)(results), vindex
    elif isinstance(value, dict):
      rdict = dict()
      for k, dvalue in value.items():
        rvalue, vindex = self._generate_retval_result(fname, dvalue, vindex, tmp_names)
        rdict[k] = rvalue

      return rdict, vindex

    if vindex == len(tmp_names):
      rvname = self._revgen.newname(fname)
      tmp_names.append(rvname)
    elif vindex < len(tmp_names):
      rvname = tmp_names[vindex]
    else:
      pyu.fatal(f'Value index out of range: {vindex} vs {len(tmp_names)}')

    var = self.load_var(rvname, ctx=ast.Store())
    if var is _NONE and isinstance(value, Value):
      var = self._new_variable(rvname, value)
    self._assign_value(var, value, rvname)

    return self.load_var(rvname, ctx=ast.Load()), vindex + 1

  def _generate_retlist_result(self, fname, return_values):
    tmp_names, results, sig = [], [], None
    for i, retval in enumerate(return_values):
      with self._emitter.placement(retval.placement):
        vsig = pycu.signature(retval.value)
        if sig is not None and not pycu.equal_signature(sig, vsig):
          pyu.fatal(f'Return values signature mismatch: {vsig} vs. {sig}')
        sig = vsig

        rvalue, _ = self._generate_retval_result(fname, retval.value, 0, tmp_names)
        results.append(rvalue)

    return results[0]

  def _run_function_helper(self, func, args, kwargs):
    func_self = getattr(func, '__self__', None)
    func = getattr(func, '__wrapped__', func)

    sig = inspect.signature(func)
    pyu.mlog(lambda: f'Signature: {sig}')

    fninfo = get_function_info(func)
    pyu.mlog(lambda: f'Source: {fninfo.filename} @ {fninfo.lineno}\n{fninfo.source}')

    func_node = ast.parse(fninfo.source, filename=fninfo.filename, mode='exec')

    func_node = ast_hdl_transform(func_node)
    pyu.mlog(lambda: f'FUNC AST: {asu.dump(func_node)}')

    func_locals = dict()
    if func_self is not None:
      args = [func_self] + args

    kwargs = self._populate_args_locals(sig, args, kwargs, func_locals)
    func_locals.update(**kwargs)

    func_body = self._get_function_body(pyu.func_name(func), func_node)

    frame = _Frame(get_obj_globals(func),
                   func_locals,
                   _SourceLocation(fninfo.filename, fninfo.lineno))
    with self._frame(frame):
      try:
        for bnode in func_body:
          self.visit(bnode)
      except _ReturnException as rex:
        frame.retval = rex.value

    if frame.return_values:
      # This handles the case of return statements from within an HDL function.
      # As all the HDL functions gets inlined, there is not really a "return", so
      # the returned values get stored into a temporary, and a "load" of that temporary
      # returned from this API.
      result = self._generate_retlist_result(pyu.func_name(func), frame.return_values)
    else:
      result = frame.yields if frame.yields else frame.retval

    pyu.mlog(lambda: f'RESULT: {result}\tEXIT LOCALS: {pyu.stri(func_locals)}')

    return result

  def _run_class_function(self, func, args, kwargs):
    pyu.mlog(lambda: f'OBJECT CREATE: class={pyu.func_name(func)} args={pyu.stri(args)} ' \
             f'kwargs={pyu.stri(kwargs)}')
    obj = func.__new__(func, *args, **kwargs)
    init = getattr(func, '__init__', None)
    if init is not None:
      self._run_function_helper(init, [obj] + args, kwargs)

    return obj

  def _call_direct(self, func, args, kwargs):
    pyu.mlog(lambda: f'DIRECT CALL: function={pyu.func_name(func)} args={pyu.stri(args)} ' \
             f'kwargs={pyu.stri(kwargs)}')

    # Do not call func(*args, **kwargs) directly as we need to insert the current
    # locals and globals.
    self.locals.update(__func=func, __args=args, __kwargs=kwargs)

    return eval('__func(*__args, **__kwargs)', self.globals, self.locals)

  def _is_hdl_function(self, func):
    if is_hdl_function(func):
      return True
    elif not inspect.isclass(func):
      return False

    init = getattr(func, '__init__', None)
    return init is not None and is_hdl_function(init)

  def run_function(self, func, args, kwargs=None):
    kwargs = kwargs or dict()
    if self._is_hdl_function(func):
      if inspect.isclass(func):
        # Running a function with a class function object, means object creation.
        result = self._run_class_function(func, args, kwargs)
      else:
        result = self._run_function_helper(func, args, kwargs)

      return result

    return self._call_direct(func, args, kwargs)


class CodeGen(_ExecVisitor):

  def __init__(self, emitter, globs):
    super().__init__(globs)
    self._emitter = emitter
    self._module_decls_place = emitter.emit_placement()
    self._used_entities = set()
    self._generated_entities = set()
    self._ent_versions = EntityVersions()
    self._vars_places = []
    self._root_vars = dict()
    self._process_kind = None
    self._process_args = None

  def _get_format_parts(self, fmt, kwargs):

    def mapfn(tok):
      arg = self._emitter.eval_token(tok)
      if arg is None:
        varg = self.run_code(tok, kwargs, 'eval',
                             filename=self.location.filename,
                             lineno=self.location.lineno)
        return self._emitter.eval_tostring(varg)

      return arg

    def nmapfn(tok):
      return self._emitter.quote_string(tok)

    return pyu.sreplace(_CODEFMT_RX, fmt, mapfn, nmapfn=nmapfn, join=False)

  def _resolve_code(self, code, kwargs):

    def mapfn(tok):
      arg = self._emitter.eval_token(tok)
      if arg is None:
        varg = self.run_code(tok, kwargs, 'eval',
                             filename=self.location.filename,
                             lineno=self.location.lineno)
        return self._emitter.svalue(varg)

      return arg

    return pyu.sreplace(_CODEFMT_RX, code, mapfn)

  def visit_default(self, node):
    # This is the default handler when a specific visit_XXX() method does not exist.
    # If something is not working, look for 'FAST STATIC' within the logs, which will
    # tell which node is escaping from the PyXHDL interpreter.
    pyu.mlog(lambda: f'FAST STATIC: {asu.dump(node)}')
    self._static_eval(node)

  def load_var(self, name, ctx=ast.Load()):
    var = vload(name, self.globals, self.locals)
    if var is _NONE:
      shvar = self._root_vars.get(name, None)
      if shvar is not None:
        var = Value(shvar.dtype, value=Ref(name, vspec=shvar.vspec), isreg=shvar.isreg)
      elif isinstance(ctx, ast.Load):
        pyu.fatal(f'Undefined variable: {name}')

    return self._emitter.var_remap(var, isinstance(ctx, ast.Store))

  def _new_variable(self, name, value):
    vinit = value.init
    if vinit is not None:
      init, vspec, isreg = vinit.value, vinit.vspec, value.isreg
    else:
      init, vspec, isreg = None, None, True

    vname = self._revgen.newname(name, shortzero=True)

    var = Value(value.dtype, value=Ref(vname, vspec=vspec), isreg=isreg)
    self._add_variable(vname, var.dtype, var.isreg, init=init, vspec=vspec)
    self._store_value(name, var)

    return var

  def _assign_value(self, var, value, name):
    pyu.mlog(lambda: f'ASSIGN: {var} ({name}) = {value}')

    if not isinstance(var, Value):
      if isinstance(value, Value) and value.init is not None:
        var = self._new_variable(name, value)
    elif name is not None and var.ref is None:
      var = None

    if isinstance(var, Value):
      if isinstance(value, Value) and (value.value is None or isinstance(value.value, Init)):
        if value.isreg != var.isreg:
          logging.warning(f'Cannot create "{var.name}" as {valkind(value.isreg)}, ' \
                          f'will be {valkind(var.isreg)}')
        if isinstance(value.value, Init):
          pyu.mlog(lambda: f'ASSIGN CREATE: {name} is {value.dtype} = {value.value}')
        else:
          pyu.mlog(lambda: f'ASSIGN CREATE: {name} is {value.dtype}')
      else:
        if is_ro_ref(var):
          pyu.fatal(f'{var.name} is read-only')

        self._emitter.emit_assign(var, name, value)
    elif name is not None:
      stg_value = value.deref() if isinstance(value, Value) else value
      self._store_value(name, stg_value)

  def _multi_assign_inner(self, target, value):
    elts = elements(target)
    if elts is not None:
      for el, val in zip(elts, value):
        self._multi_assign_inner(el, val)
    else:
      var = self.eval_node(target)
      if isinstance(var, _Storer):
        var.store(value)
      else:
        name = target.id if isinstance(target, ast.Name) else None
        self._assign_value(var, value, name)

  def _multi_assign(self, targets, value):
    for target in targets:
      self._multi_assign_inner(target, value)

  def assign_value(self, name, value):
    self._assign_value(self.load_var(name, ctx=ast.Store()), value, name)

  def _unpack_value(self, targets, values, dest):
    if isinstance(targets, ast.Name):
      dest[targets.id] = values
    else:
      elts = elements(targets)
      if elts:
        for t, v in zip(elts, values):
          self._unpack_value(t, v, dest)

  def _handle_array(self, node, atype):
    pyu.mlog(lambda: asu.dump(node))
    values = []
    for n in node.elts:
      xn = self.eval_node(n)
      values.append(xn)

    self.push_result(atype(values))

  def _prepare_call_arg(self, arg):
    return make_ro_ref(arg) if isinstance(arg, Value) else arg

  def _handle_call(self, func, args, kwargs):
    if pyu.is_subclass(func, Entity):
      pyu.mlog(lambda: f'Entity instantiation: {pyu.func_name(func)} args={pyu.stri(args)} ' \
               f'kwargs={pyu.stri(kwargs)}')
      # We do not run the Entity init code with run_function() as this is not what
      # we want. Doing so will end up emitting HDL code.
      # Entities constructors cannot perform operations which lead to HDL code emission.
      # Note that HDL type manipulation is OK, as this will not emit HDL code.
      result = func(*args, **kwargs)

      ent_name = self._register_entity(func, kwargs)

      self._emitter.emit_entity(result, kwargs, ent_name=ent_name)
    else:
      result = self.run_function(func, args, kwargs=kwargs)

    return result

  def _process_scope_enter(self, vars_scope, process_kind, process_args):
    self._variables.append(dict())
    self._vars_places.append(vars_scope)
    self._process_kind = process_kind
    self._process_args = process_args

  def _process_scope_exit(self):
    pyu.mlog(lambda: f'Variables stack is {len(self._variables)} deep')

    vars = self._variables.pop()
    place = self._vars_places.pop()

    root_vars = dict()
    with self._emitter.placement(place) as emt:
      for name, var in vars.items():
        if emt.is_root_variable(var):
          root_vars[name] = var
        else:
          pyu.mlog(lambda: f'VARIABLE: {valkind(var.isreg)} {var.dtype} {name}')
          emt.emit_declare_variable(name, var)

    with self._emitter.placement(self._emitter.module_vars_place) as emt:
      for name, var in root_vars.items():
        shv = self._root_vars.get(name, None)
        if shv is not None:
          if shv != var:
            pyu.fatal(f'Root variable declaration mismatch: {pyu.stri(var)} vs. {pyu.stri(shv)}')
        else:
          pyu.mlog(lambda: f'ROOT VARIABLE: {valkind(var.isreg)} {var.dtype} {name}')
          emt.emit_declare_variable(name, var)

    self._root_vars.update(**root_vars)

  def _register_entity(self, eclass, kwargs, generated=False):
    pargs, rkwargs = dict(), kwargs.copy()
    for pin in eclass.PORTS:
      arg = rkwargs.pop(pin.name, None)
      if arg is None:
        pyu.fatal(f'Missing entity port "{pin.name}" binding for entity {eclass.__name__}')

      verify_port_arg(pin, arg)
      pargs[pin.name] = arg.new_value(make_port_ref(pin))

    for kwarg_name, arg in eclass.ARGS.items():
      rkwargs[kwarg_name] = rkwargs.get(kwarg_name, arg)

    ename = eclass.NAME
    if ename is None:
      # External entities do not need to be regsitered, as no generation needs to happen for them.
      # Their name also, is always the one specified within the Entity subclass declaration.
      ename, erec = self._ent_versions.getname(eclass, pargs, {k: wrap(v) for k, v in rkwargs.items()})
      self._used_entities.add(erec)
      if generated:
        self._generated_entities.add(erec)

    return ename

  def _get_sensitivity(self, hdl_args, din):
    def expand(v, dest):
      if isinstance(v, dict):
        dest.update(v)
      elif isinstance(v, str):
        for port in pyu.resplit(v, ','):
          sargs = dict()
          if port.startswith('+'):
            sargs['trigger'] = POSEDGE
            port = port[1: ]
          elif port.startswith('-'):
            sargs['trigger'] = NEGEDGE
            port = port[1: ]

          dest[port] = Sens(**sargs)
      elif isinstance(v, (list, tuple)):
        for x in v:
          expand(x, dest)

      return dest

    sensitivity = expand(hdl_args.get('sens', dict()), dict())

    for name, sens in sensitivity.items():
      if name not in din:
        pyu.fatal(f'Sensitivity source is not a port: {name}')
      pyu.mlog(lambda: f'Sensitivity: {name} {TRIG_NAME[sens.trigger]}')

    return sensitivity

  def generate_entity(self, eclass, eargs):
    pyu.mlog(lambda: f'Entity {eclass.__name__}')

    ent_name = self._register_entity(eclass, eargs, generated=True)

    kwargs = eargs.copy()
    args, din, cargs = [], dict(), dict()
    for pin in eclass.PORTS:
      pyu.mlog(lambda: f'Port: {pin.name} {IO_NAME[pin.idir]}')

      arg = kwargs.pop(pin.name, None)
      if arg is None:
        pyu.fatal(f'Missing argument "{pin.name}" for Entity "{eclass.__name__}"')

      ref = make_port_ref(pin)
      if isinstance(arg, Value):
        port_arg = arg.new_value(ref)
      else:
        if not isinstance(arg, Type): pyu.fatal(f'Argument must be Type at this point: {arg}')
        port_arg = mkwire(arg, name=ref)

      args.append(self._emitter.make_port_arg(port_arg))

      din[pin.name] = pin
      cargs[pin.name] = args[-1]

    for kwarg_name, arg in eclass.ARGS.items():
      rarg = kwargs.get(kwarg_name, arg)
      kwargs[kwarg_name] = rarg

      pyu.mlog(lambda: f'Arg: {kwarg_name} = {rarg}')

    uw_kwargs = {k: unwrap(v) for k, v in kwargs.items()}
    ent_args = pyu.dmerge(cargs, uw_kwargs)

    ent = eclass(**ent_args)

    ecomm = f'Entity "{ent_name}" is "{eclass.__name__}" with:\n' \
      f'\targs={({k: pyu.stri(v.dtype if isinstance(v, Value) else v) for k, v in cargs.items()})}\n' \
      f'\tkwargs={pyu.stri(ent.kwargs)}'

    with self._emitter.placement(self._module_decls_place) as emt:
      emt.emit_module_def(ent_name, ent, comment=ecomm)

    self._emitter.emit_module_decl(ent_name, ent)
    self._root_vars = dict()
    self._revgen = pyu.RevGen()

    for func in ent.enum_processes():
      hdl_args = get_hdl_args(func) or dict()

      pyu.mlog(lambda: f'Process function: {pyu.func_name(func)}')

      sensitivity = self._get_sensitivity(hdl_args, din)
      process_kind = hdl_args.get('kind', None)

      with self._emitter.indent():
        # Process functions will automatically see port names as locals, so the
        # position arguments list is empty. Process functions can still have keyword
        # arguments, which will be correctly populated.
        self.generate_process(func, [],
                              kwargs=ent_args,
                              sensitivity=sensitivity,
                              process_kind=process_kind,
                              process_args=hdl_args)

    self._emitter.emit_module_end()

  def generate_process(self, func, args, kwargs=None, sensitivity=None,
                       process_kind=None, process_args=None):
    if process_kind == ROOT_PROCESS:
      self._process_scope_enter(self._emitter.module_vars_place, process_kind,
                                process_args)
      try:
        result = self.run_function(func, args, kwargs=kwargs)
      finally:
        self._process_scope_exit()
    else:
      self._emitter.emit_process_decl(pyu.func_name(func),
                                      sensitivity=sensitivity,
                                      process_kind=process_kind,
                                      process_args=process_args)

      self._emitter.emit_process_begin()
      self._process_scope_enter(self._emitter.process_vars_place, process_kind,
                                process_args)
      try:
        with self._emitter.indent():
          result = self.run_function(func, args, kwargs=kwargs)
      finally:
        self._process_scope_exit()
      self._emitter.emit_process_end()

    return result

  def _flush_generation(self):
    while True:
      used_entities = self._used_entities.copy()
      generated = 0
      for erec in used_entities:
        if erec not in self._generated_entities:
          self.generate_entity(erec.eclass, pyu.dmerge(erec.pargs, erec.kwargs))
          generated += 1

      if generated == 0:
        break

  def visit_Constant(self, node):
    self.push_result(node.value)

  def visit_FormattedValue(self, node):
    self.push_result(self._static_eval(node))

  def visit_JoinedStr(self, node):
    self.push_result(self._static_eval(node))

  def visit_Tuple(self, node):
    self._handle_array(node, tuple)

  def visit_List(self, node):
    self._handle_array(node, list)

  def visit_Set(self, node):
    pyu.mlog(lambda: asu.dump(node))
    result = set()
    for snode in node.elts:
      result.add(self.eval_node(snode))

    self.push_result(result)

  def visit_Dict(self, node):
    pyu.mlog(lambda: asu.dump(node))
    result = dict()
    for knode, vnode in zip(node.keys, node.values):
      k = self.eval_node(knode)
      v = self.eval_node(vnode)
      result[k] = v

    self.push_result(result)

  def visit_Name(self, node):
    pyu.mlog(lambda: asu.dump(node))
    result = self.load_var(node.id, ctx=node.ctx)
    self.push_result(result)

  def visit_Expression(self, node):
    value = self.eval_node(node.body)
    self.push_result(value)

  def visit_Expr(self, node):
    value = self.eval_node(node.value)
    self.push_result(value)

  def visit_UnaryOp(self, node):
    operand = self.eval_node(node.operand)
    if has_hdl_vars(operand):
      result = self._emitter.eval_UnaryOp(node.op, operand)
    else:
      result = self._static_eval(node)

    self.push_result(result)

  def _neval(self, ref_node, cls, **kwargs):
    snode = cls(**kwargs)
    ast.copy_location(snode, ref_node)

    return self._static_eval(snode)

  def visit_BinOp(self, node):
    left = self.eval_node(node.left)
    right = self.eval_node(node.right)
    if has_hdl_vars((left, right)):
      result = self._emitter.eval_BinOp(node.op, left, right)
    else:
      result = self._static_eval(node)

    self.push_result(result)

  def visit_BoolOp(self, node):
    values = []
    for val in node.values:
      xval = self.eval_node(val)
      values.append(xval)

    if has_hdl_vars(values):
      result = self._emitter.eval_BoolOp(node.op, values)
    else:
      result = self._static_eval(node)

    self.push_result(result)

  def visit_Compare(self, node):
    left = self.eval_node(node.left)
    comparators = []
    for comp in node.comparators:
      xcomp = self.eval_node(comp)
      comparators.append(xcomp)

    if has_hdl_vars((left, comparators)):
      result = self._emitter.eval_Compare(left, node.ops, comparators)
    else:
      result = self._static_eval(node)

    self.push_result(result)

  def visit_Lambda(self, node):
    pyu.mlog(lambda: asu.dump(node))

    flocals = self.locals

    def lambda_runner(*args, **kwargs):
      func_locals = flocals.copy()

      for p, arg in zip(node.args.args, args):
        func_locals[p.arg] = arg

      func_locals.update(**kwargs)

      with self._frame(self.frame.new_locals(func_locals)):
        result = self.eval_node(node.body)

      pyu.mlog(lambda: f'LM RESULT {result}\tLOCALS: {pyu.stri(func_locals)}')

      return result

    self.push_result(lambda_runner)

  def visit_Call(self, node):
    func = self.eval_node(node.func)

    args = []
    for carg in node.args:
      if isinstance(carg, ast.Starred):
        value = self.eval_node(carg.value)
        for svalue in elements(value):
          args.append(self._prepare_call_arg(svalue))
      else:
        value = self.eval_node(carg)
        args.append(self._prepare_call_arg(value))

    kwargs = dict()
    for kwarg in node.keywords:
      kwval = self.eval_node(kwarg.value)
      if kwarg.arg:
        kwargs[kwarg.arg] = self._prepare_call_arg(kwval)
      else:
        if not isinstance(kwval, dict): pyu.fatal(f'Wrong type: {type(kwval)}')
        for name, value in kwval.items():
          kwargs[name] = self._prepare_call_arg(value)

    pyu.mlog(lambda: f'CALL: {func}\t{pyu.stri(args)}\t{pyu.stri(kwargs)}')

    result = self._handle_call(func, args, kwargs)

    self.push_result(result)

  def _load_subs_attr(self, node, ctx):
    if isinstance(node, ast.Name):
      return self.load_var(node.id, ctx=ctx)

    return self.eval_node(node)

  def visit_Attribute(self, node):
    value = self._load_subs_attr(node.value, node.ctx)
    if isinstance(node.ctx, ast.Load):
      result = getattr(value, node.attr)
    elif isinstance(node.ctx, ast.Store):
      if isinstance(value, Value) and is_ro_ref(value):
        pyu.fatal(f'{value.name} is read-only')

      result = _StoreAttribute(value, node.attr)
    else:
      pyu.fatal(f'Unknown subscript context type: {asu.dump(node.ctx)}')

    self.push_result(result)

  def visit_NamedExpr(self, node):
    value = self.eval_node(node.value)
    var = self.load_var(node.target.id, ctx=node.target.ctx)
    self._assign_value(var, value, node.target.id)

  def visit_Subscript(self, node):
    value = self._load_subs_attr(node.value, node.ctx)
    if isinstance(value, Value) and isinstance(node.ctx, ast.Store) and is_ro_ref(value):
      pyu.fatal(f'{value.name} is read-only')

    sv = self.eval_node(node.slice)
    if isinstance(value, Value):
      result = self._emitter.eval_Subscript(value, sv)
    elif isinstance(node.ctx, ast.Load):
      result = value[sv]
    elif isinstance(node.ctx, ast.Store):
      result = _StoreSubscript(value, sv)
    else:
      pyu.fatal(f'Unknown subscript context type: {asu.dump(node.ctx)}')

    self.push_result(result)

  def visit_Slice(self, node):
    lower = self.eval_node(node.lower) if node.lower is not None else None
    upper = self.eval_node(node.upper) if node.upper is not None else None
    step = self.eval_node(node.step) if node.step is not None else None
    if has_hdl_vars((lower, upper, step)):
      pyu.fatal(f'Slice cannot have HDL arguments: {asu.dump(node)}')

    self.push_result(slice(lower, upper, step))

  def _walk_generator(self, node, fn):
    for gen in node.generators:
      gen_iter = self.eval_node(gen.iter)
      for xv in gen_iter:
        self.locals[gen.target.id] = xv

        ifv = True
        for ifn in gen.ifs:
          ifv = self.eval_node(ifn)
          if not ifv:
            break

        if ifv:
          fn(node)

  def visit_DictComp(self, node):
    result = dict()

    def walker(node):
      kv = self.eval_node(node.key)
      vv = self.eval_node(node.value)
      result[kv] = vv

    self._walk_generator(node, walker)

    self.push_result(result)

  def _handle_container_comp(self, node, ctype):
    result = []

    def walker(node):
      cv = self.eval_node(node.elt)
      result.append(cv)

    self._walk_generator(node, walker)

    if not isinstance(result, ctype):
      result = ctype(result)

    self.push_result(result)

  def visit_ListComp(self, node):
    self._handle_container_comp(node, list)

  def visit_SetComp(self, node):
    self._handle_container_comp(node, set)

  def visit_GeneratorExp(self, node):
    self._handle_container_comp(node, tuple)

  def visit_Assign(self, node):
    value = self.eval_node(node.value)
    self._multi_assign(node.targets, value)

  def visit_AugAssign(self, node):
    ltarget = as_loading(node.target)
    ref_value = self.eval_node(ltarget)
    value = self.eval_node(node.value)

    if has_hdl_vars((ref_value, value)):
      result = self._emitter.eval_BinOp(node.op, ref_value, value)
    else:
      result = self._neval(node, ast.BinOp, op=node.op, left=ltarget, right=node.value)

    self._multi_assign([node.target], result)

  def visit_Raise(self, node):
    exc = self.eval_node(node.exc)
    raise exc

  def visit_Assert(self, node):
    test = self.eval_node(node.test)
    msg = self.eval_node(node.msg) if node.msg is not None else None

    if has_hdl_vars(test):
      parts = self._get_format_parts(msg, dict()) if msg else None
      self._emitter.emit_Assert(test, parts)
    elif not test:
      pyu.fatal(msg, exc=AssertionError)

  def visit_Module(self, node):
    # This handler simply dive into inner nodes by calling the AST Visitor
    # generic_visit() API (after some logging we do to make sense of what is
    # being processed).
    self.eval_node(node, visit_node=False)

  def visit_IfExp(self, node):
    test = self.eval_node(node.test)
    if has_hdl_vars(test):
      body = self.eval_node(node.body)
      orelse = self.eval_node(node.orelse)
      result = self._emitter.eval_IfExp(test, body, orelse)
    else:
      if test:
        result = self.eval_node(node.body)
      else:
        result = self.eval_node(node.orelse)

    self.push_result(result)

  def visit_If(self, node):
    test = self.eval_node(node.test)

    if has_hdl_vars(test):
      with self._hdl_branch():
        self._emitter.emit_If(test)
        with self._emitter.indent():
          for insn in node.body:
            self.eval_node(insn)

        enode = node
        while len(enode.orelse) == 1 and isinstance(enode.orelse[0], ast.If):
          enode = enode.orelse[0]
          etest = self.eval_node(enode.test)
          self._emitter.emit_Elif(etest)
          with self._emitter.indent():
            for insn in enode.body:
              self.eval_node(insn)

        if enode.orelse:
          self._emitter.emit_Else()
          with self._emitter.indent():
            for insn in enode.orelse:
              self.eval_node(insn)

        self._emitter.emit_EndIf()
    else:
      pyu.mlog(lambda: f'Resolving static If test: {asu.dump(node.test)}')
      if test:
        for insn in node.body:
          self.eval_node(insn)
      else:
        for insn in node.orelse:
          self.eval_node(insn)

  def visit_For(self, node):
    pyu.mlog(lambda: asu.dump(node))

    for_iter = self.eval_node(node.iter)
    for t in for_iter:
      self._unpack_value(node.target, t, self.locals)

      got_break = False
      for insn in node.body:
        try:
          self.eval_node(insn)
        except _BreakException:
          got_break = True
          break
        except _ContinueException:
          break

      if got_break:
        break

  def visit_While(self, node):
    pyu.mlog(lambda: asu.dump(node))

    while True:
      test = self.eval_node(node.test)
      if has_hdl_vars(test):
        pyu.fatal(f'While test cannot have HDL vars: {asu.dump(node.test)}')

      if test:
        got_break = False
        for insn in node.body:
          try:
            self.eval_node(insn)
          except _BreakException:
            got_break = True
            break
          except _ContinueException:
            break

        if got_break:
          break
      else:
        break

  def visit_Break(self, node):
    pyu.mlog(lambda: asu.dump(node))
    raise _BreakException()

  def visit_Continue(self, node):
    pyu.mlog(lambda: asu.dump(node))
    raise _ContinueException()

  def visit_Try(self, node):
    try:
      for bnode in node.body:
        self.visit(bnode)
    except Exception as e:
      pyu.mlog(lambda: f'Caught exception: {e}')
      for xhand in node.handlers:
        xtype = self.eval_node(xhand.type)
        if isinstance(e, xtype):
          if xhand.name:
            self.locals[xhand.name] = e
          for bnode in xhand.body:
            self.visit(bnode)

          break
    else:
      for enode in node.orelse:
        self.visit(enode)
    finally:
      for fnode in node.finalbody:
        self.visit(fnode)

  def visit_With(self, node):
    items, names = [], []
    for inode in node.items:
      item = self.eval_node(inode.context_expr)
      name = inode.optional_vars.id if isinstance(inode.optional_vars, ast.Name) else None
      items.append(item)
      names.append(name)

    bi, bitems, rex = 0, [], None
    try:
      while bi < len(items):
        bitem = items[bi].__enter__()
        bitems.append(bitem)
        bi += 1

      for name, bitem in zip(names, bitems):
        if name is not None:
          self.locals[name] = bitem

      for bnode in node.body:
        self.eval_node(bnode)

    except Exception as ex:
      rex = ex

    wex = None
    bi -= 1
    while bi >= 0:
      if rex is not None:
        if not items[bi].__exit__(type(rex), rex, rex.__traceback__):
          wex = rex
      else:
        items[bi].__exit__(None, None, None)
      bi -= 1

    if wex is not None:
      raise wex

  def visit_Return(self, node):
    pyu.mlog(lambda: asu.dump(node))
    value = self.eval_node(node.value) if node.value is not None else None
    if self.frame.in_hdl_branch:
      retval = _Return(value=value, placement=self._emitter.emit_placement())
      self.frame.return_values.append(retval)
    else:
      raise _ReturnException(value)

  def visit_Yield(self, node):
    # Yielded values are accumulated into yields list setup by the function call
    # processing. This is different from how they are implemented in CPython but
    # they are much easier to implement.
    pyu.mlog(lambda: asu.dump(node))
    value = self.eval_node(node.value)
    self.push_yield(value)

  def visit_Global(self, node):
    for name in node.names:
      self.global_names.add(name)

  def visit_Match(self, node):
    subject = self.eval_node(node.subject)
    cases = []
    for mc in node.cases:
      pattern = self.eval_node(mc.pattern)
      scope = self._emitter.create_placement(extra_indent=2)
      with self._emitter.placement(scope):
        for insn in mc.body:
          self.eval_node(insn)

      for ptrn in pyu.as_sequence(pattern, t=(tuple, list)):
        cases.append(_MatchCase(pattern=ptrn, scope=scope))

    self._emitter.emit_match_cases(subject, cases)

  def visit_MatchAs(self, node):
    pyu.mlog(lambda: asu.dump(node))
    if node.pattern:
      result = self.eval_node(node.pattern)
      assert node.name is None, 'TBH'
    elif node.name:
      result = self.load_var(node.name, ctx=ast.Load())
    else:
      # None match means "everything else".
      result =  None

    self.push_result(result)

  def visit_MatchValue(self, node):
    pyu.mlog(lambda: asu.dump(node))
    result = self.eval_node(node.value)
    self.push_result(result)

  def visit_MatchSequence(self, node):
    pyu.mlog(lambda: asu.dump(node))
    patterns = []
    for ptrn in node.patterns:
      value = self.eval_node(ptrn)
      patterns.append(value)

    self.push_result(patterns)

  @property
  def emitter(self):
    return self._emitter

  @staticmethod
  def current():
    return pyu.get_context(_CGENCTX)

  def context(self):
    return pyu.Context(_CGENCTX, self)

  def run_code(self, code, args, mode, filename=None, lineno=None):
    if filename is None:
      filename, lineno = pyiu.parent_coords()

    cnode = ast.parse(code, filename=filename, mode=mode)
    cnode.lineno = lineno
    ast.fix_missing_locations(cnode)

    pyu.mlog(lambda: f'RUN CODE: {asu.dump(cnode)}')

    if mode == 'exec':
      with self._exec_locals(args):
        return self.eval_node(cnode)
    elif mode == 'eval':
      with self._eval_locals(args):
        return self.eval_node(cnode)
    else:
      raise RuntimeError(f'Invalid mode: {mode}')

  def flush(self):
    self._flush_generation()
    return self._emitter.flush()

  def emit_code(self, code, **kwargs):
    dcode = textwrap.dedent(code)
    pyu.mlog(lambda: f'INLINE CODE:\n{dcode}')

    hcode = self._resolve_code(dcode, kwargs)
    self._emitter.emit_code(hcode)

  def emit_report(self, fmt, **kwargs):
    parts = self._get_format_parts(fmt, kwargs)

    self._emitter.emit_report(parts, **kwargs)

  def emit_write(self, fmt, **kwargs):
    parts = self._get_format_parts(fmt, kwargs)

    self._emitter.emit_write(parts, **kwargs)

  def emit_call(self, fname, args, dtype):
    return self._emitter.emit_call(fname, args, dtype)

  def mkvwire(self, dtype, value, **iargs):
    vspec = pyu.make_ntuple(VSpec, iargs) if iargs else None

    return Wire(dtype, value=Init(value=value, vspec=vspec))

  def mkvreg(self, dtype, value, **iargs):
    vspec = pyu.make_ntuple(VSpec, iargs) if iargs else None

    return Register(dtype, value=Init(value=value, vspec=vspec))

  def emitter_context(self, **kwargs):
    return self._emitter.context(kwargs)

  def no_hdl(self):
    def infn():
      self.add_catchall(self._static_eval)
      return self

    def outfn(*exc):
      self.pop_catchall()
      return False

    return pycm.CtxManager(infn, outfn)

