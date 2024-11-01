import py_misc_utils.utils as pyu


def _add_inputs(inseq, gglobals, ddict):
  for ein in inseq:
    names, expr = ein.split('=', 1)
    value = eval(expr, gglobals)
    for name in pyu.comma_split(names):
      pyu.dict_add(ddict, name, value)


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
  cfg = pyu.load_config(cfg_file=args.cfgfile)
  for k, v in cfg.items():
    setattr(args, k, v)

