import re

import py_misc_utils.utils as pyu


def _add_inputs(inseq, gglobals, dest):
  for ein in inseq:
    names, expr = re.split(r'\s*=\s*', ein, maxsplit=1)

    try:
      value = eval(expr, gglobals)
    except:
      value = expr

    for name in pyu.comma_split(names):
      pyu.dict_rset(dest, name, value)


def parse_kwargs(kwargs, gglobals, dest=None):
  dest = pyu.value_or(dest, dict())
  if kwargs:
    _add_inputs(kwargs, gglobals, dest)

  return dest


def parse_inputs(inputs, kwargs, gglobals):
  dest = dict()
  if inputs:
    _add_inputs(inputs, gglobals, dest)

  return parse_kwargs(kwargs, gglobals, dest=dest)


def parse_args(cfgfile, args):
  cfg = pyu.load_config(args.cfgfile)
  for k, v in cfg.items():
    setattr(args, k, v)

