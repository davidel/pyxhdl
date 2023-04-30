import logging
import yaml
import sys

import py_misc_utils.utils as pyu


def _add_inputs(inseq, gglobals, ddict):
  for ein in inseq:
    names, expr = ein.split('=', 1)
    value = eval(expr, gglobals)
    for name in names.split(','):
      pyu.dict_add(ddict, name.strip(), value)


def parse_kwargs(kwargs, gglobals, ddict=None):
  ddict = dict() if ddict is None else ddict
  if kwargs:
    _add_inputs(kwargs, gglobals, ddict)

  return ddict


def parse_inputs(inputs, kwargs, gglobals):
  ddict = dict()
  if inputs:
    _add_inputs(inputs, gglobals, ddict)

  return parse_kwargs(kwargs, gglobals, ddict=ddict)


def parse_args(cfgfile, args):
  with open(args.cfgfile, mode='r') as cfd:
    cfg = yaml.load(cfd)

  for k, v in cfg.items():
    setattr(args, k, v)


def output_file(path, mode='w'):
  return open(path, mode=mode) if path is not None else sys.stdout

