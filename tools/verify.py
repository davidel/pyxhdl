import argparse
import collections
import logging
import os
import re
import shutil
import string
import subprocess
import tempfile

import py_misc_utils.utils as pyu


class Verifier(object):

  def __init__(self, xpath, cmdline_args):
    self._xpath = xpath
    self._args = cmdline_args


class VivadoVerifier(Verifier):

  CMDLINE = '-mode batch -nolog -nojournal -source'

  def __init__(self, xpath, cmdline_args):
    super().__init__(xpath, cmdline_args)

  def _create_tcl_script(self, fd, files, backend, top_entity):
    if backend == 'VHDL':
      fd.write(f'read_vhdl -vhdl2008 {{' + ', '.join(files) + f'}}\n')
    elif backend == 'Verilog':
      fd.write(f'read_verilog {{' + ', '.join(files) + f'}}\n')
    else:
      pyu.fatal(f'Unknown backend: {backend}')

    fd.write(f'synth_design -top {top_entity}\n')

  @property
  def name(self):
    return 'Vivado'

  def verify(self, files, backend, top_entity):
    with tempfile.TemporaryDirectory() as tmp_path:
      fd, path = tempfile.mkstemp(dir=tmp_path, suffix='.tcl', text=True)
      tfd = os.fdopen(fd, mode='wt')
      self._create_tcl_script(tfd, files, backend, top_entity)
      tfd.close()

      cmdline = re.split(r'\s+', string.Template(self.CMDLINE).substitute())

      try:
        output = subprocess.check_output([self._xpath] + cmdline + [path],
                                         stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as ex:
        pyu.fatal(f'Verification process exited with {ex.returncode} code. ' \
                  f'Error output:\n' + ex.output.decode())

      return output


class GhdlVerifier(Verifier):

  CMDLINE = '-a --std=08 --workdir=$WORKDIR -frelaxed -Wno-shared'

  def __init__(self, xpath, cmdline_args):
    super().__init__(xpath, cmdline_args)

  @property
  def name(self):
    return 'GHDL'

  def verify(self, files, backend, top_entity):
    with tempfile.TemporaryDirectory() as tmp_path:
      cmdline = re.split(r'\s+', string.Template(self.CMDLINE).substitute(WORKDIR=tmp_path))

      try:
        output = subprocess.check_output([self._xpath] + cmdline + list(files),
                                         stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as ex:
        pyu.fatal(f'Verification process exited with {ex.returncode} code. ' \
                  f'Error output:\n' + ex.output.decode())

      return output


class VerilatorVerifier(Verifier):

  CMDLINE = '--lint-only -Wall --timing --top $TOP'

  def __init__(self, xpath, cmdline_args):
    super().__init__(xpath, cmdline_args)

  @property
  def name(self):
    return 'Verilator'

  def verify(self, files, backend, top_entity):
    with tempfile.TemporaryDirectory() as tmp_path:
      cmdline = re.split(r'\s+', string.Template(self.CMDLINE).substitute(TOP=top_entity))

      try:
        output = subprocess.check_output([self._xpath] + cmdline + list(files),
                                         stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as ex:
        pyu.fatal(f'Verification process exited with {ex.returncode} code. ' \
                  f'Error output:\n' + ex.output.decode())

      return output


ToolSpec = collections.namedtuple('ToolSpec', 'name, binary, tclass, backends')

VERIFY_TOOLS = {
  # Ensure you have sourced the Vivado settings shell script which sets up the
  # proper environment variables (usually named settings64.sh).
  'Vivado': ToolSpec(name='Vivado', binary='vivado', tclass=VivadoVerifier, backends='VHDL,Verilog'),
  'GHDL': ToolSpec(name='GHDL', binary='ghdl', tclass=GhdlVerifier, backends='VHDL'),
  'Verilator': ToolSpec(name='Verilator', binary='verilator', tclass=VerilatorVerifier, backends='Verilog'),
}

def _load_verifiers(args):
  verifiers = []

  exclude = set(args.exclude or [])
  for name, tspec in VERIFY_TOOLS.items():
    if name not in exclude and args.backend in re.split(r'\s*,\s*', tspec.backends):
      xpath = shutil.which(tspec.binary)
      if xpath is not None:
        verifiers.append(tspec.tclass(xpath, args))
        logging.info(f'Found {name} verifier at {xpath}')
      else:
        logging.debug(f'Unable to find binary "{tspec.binary}" for {name} verifier')

  return verifiers


def _main(args):
  verifiers = _load_verifiers(args)

  if not verifiers:
    pyu.fatal(f'Unable to find any valid HDL verification tools')

  for hver in verifiers:
    logging.info(f'Running {hver.name} verifier on {args.backend} files {args.inputs}')

    hver.verify(args.inputs, args.backend, args.entity)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='VHDL/Verilog Code Verifier',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--inputs', action='append', required=True,
                      help='The input files to be analyzed')
  parser.add_argument('--entity', type=str, required=True,
                      help='The root entity name')
  parser.add_argument('--backend', type=str, default='VHDL',
                      choices={'VHDL', 'Verilog'},
                      help='The backend to generate the code for')
  parser.add_argument('--exclude', action='append',
                      choices={'GHDL', 'Vivado'},
                      help='The list of verifiers to be excluded')
  parser.add_argument('--log_level', type=str, default='INFO',
                      choices={'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'},
                      help='The logging level')
  parser.add_argument('--log_file', type=str,
                      help='The log file path')

  args = parser.parse_args()
  pyu.setup_logging(log_level=args.log_level, log_file=args.log_file)
  _main(args)

