import argparse
import logging

import py_misc_utils.alog as alog
import py_misc_utils.utils as pyu

from .emitter import *
from .main_utils import *
from .pyxhdl import *
from .types import *
from .utils import *
from .vars import *
from .vhdl_emitter import *

from . import testbench as tb


def _main(args):
  if args.cfgfile is not None:
    parse_args(args.cfgfile, args)

  mod = pyu.load_module(args.input_file)
  ent_class = getattr(mod, args.entity)

  gglobals = create_globals(mod, source_globals=globals())

  ekwargs = parse_kwargs(args.ekwargs, gglobals)
  emitter = Emitter.create(args.backend, cfg_file=args.emitter_cfgfile, **ekwargs)

  codegen = CodeGen(emitter, gglobals)

  inputs = parse_inputs(args.inputs, args.kwargs, gglobals)

  with codegen.context():
    if args.testbench:
      tb.generate(codegen, args, ent_class, inputs)
    else:
      codegen.generate_entity(ent_class, inputs)

    with output_file(args.output_file) as ofd:
      for ln in codegen.flush():
        print(ln, file=ofd)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='PyXHDL Code Generator',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--input_file', type=str, required=True,
                      help='The path to the Python source file containing the root entity')
  parser.add_argument('--entity', type=str, required=True,
                      help='The root entity name')
  parser.add_argument('--backend', type=str, default='VHDL',
                      choices=set(Emitter.available()),
                      help='The backend to generate the code for')
  parser.add_argument('--inputs', action='append',
                      help='The inputs for the root entity')
  parser.add_argument('--kwargs', action='append',
                      help='The keyword arguments for the root entity')
  parser.add_argument('--emitter_cfgfile', type=str,
                      help='The path to the YAML file containing the emitter configuration')
  parser.add_argument('--ekwargs', action='append',
                      help='The keyword arguments for the emitter')
  parser.add_argument('--cfgfile', type=str,
                      help='The path to the YAML file containing the generator configuration')
  parser.add_argument('--output_file', type=str,
                      help='The path to the output file for the generated code (default STDOUT)')
  parser.add_argument('--testbench', action='store_true',
                      help='Run the entity with a testbench')

  alog.add_logging_options(parser)
  tb.add_arguments(parser)

  args = parser.parse_args()
  alog.setup_logging(args)
  _main(args)

