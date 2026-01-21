import argparse
import os
import re
import shutil
import string
import subprocess
import tempfile
import textwrap

import py_misc_utils.alog as alog
import py_misc_utils.app_main as app_main
import py_misc_utils.utils as pyu


class Verifier(object):

  def __init__(self, binary, cmdline_args):
    xpath = shutil.which(binary)
    if not xpath:
      alog.debug(f'Unable to find binary "{binary}" for {self.name} verifier')
      raise NotImplementedError(f'Unable to find binary "{binary}" for {self.name} verifier')

    alog.info(f'Found {self.name} verifier at {xpath}')

    self._binary = binary
    self._xpath = xpath
    self._args = cmdline_args

  def _make_subs_ctx(self, files, backend, top_entity, **kwargs):
    sctx = {
      'CSFILES': ', '.join(files),
      'SFILES': ' '.join(files),
      'TOP': top_entity,
      'BACKEND': backend,
    }
    sctx.update(kwargs)

    return sctx


class VivadoVerifier(Verifier):

  BINARY = 'vivado'
  CMDLINE = '-mode batch -nolog -nojournal -source'

  def __init__(self, cmdline_args):
    super().__init__(self.BINARY, cmdline_args)
    self._backend_read = {
      'verilog': ['read_verilog -sv {{ $CSFILES }}'],
      'vhdl': ['read_vhdl -vhdl2008 {{ $CSFILES }}'],
    }

  def _create_script(self, files, backend):
    script = list(self._backend_read[backend])

    script.append('synth_design -top $TOP')

    return '\n'.join(script)

  @property
  def name(self):
    return 'Vivado'

  @property
  def backends(self):
    return ('verilog', 'vhdl')

  def verify(self, files, backend, top_entity):
    with tempfile.TemporaryDirectory() as tmp_path:
      script = self._create_script(files, backend)

      sctx = self._make_subs_ctx(files, backend, top_entity)

      script = string.Template(script).substitute(**sctx)

      alog.debug(f'Vivado Script:\n{textwrap.indent(script, "  ")}')

      fd, path = tempfile.mkstemp(dir=tmp_path, suffix='.tcl', text=True)
      with os.fdopen(fd, mode='wt') as tfd:
        tfd.write(script)

      cmdline = re.split(r'\s+', string.Template(self.CMDLINE).substitute(**sctx))

      try:
        output = subprocess.check_output([self._xpath] + cmdline + [path],
                                         stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as ex:
        pyu.fatal(f'Verification process exited with {ex.returncode} code. ' \
                  f'Error output:\n' + ex.output.decode())

      return output


class GhdlVerifier(Verifier):

  BINARY = 'ghdl'
  CMDLINE = '-a --std=08 --workdir=$WORKDIR -frelaxed -Wno-shared'

  def __init__(self, cmdline_args):
    super().__init__(self.BINARY, cmdline_args)

  @property
  def name(self):
    return 'GHDL'

  @property
  def backends(self):
    return ('vhdl',)

  def verify(self, files, backend, top_entity):
    with tempfile.TemporaryDirectory() as tmp_path:
      sctx = self._make_subs_ctx(files, backend, top_entity,
                                 WORKDIR=tmp_path)

      cmdline = re.split(r'\s+', string.Template(self.CMDLINE).substitute(**sctx))

      try:
        output = subprocess.check_output([self._xpath] + cmdline + list(files),
                                         stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as ex:
        pyu.fatal(f'Verification process exited with {ex.returncode} code. ' \
                  f'Error output:\n' + ex.output.decode())

      return output


class VerilatorVerifier(Verifier):

  BINARY = 'verilator'
  CMDLINE = '--lint-only -Wall --timing -Wno-DECLFILENAME -sv --top $TOP'

  def __init__(self, cmdline_args):
    super().__init__(self.BINARY, cmdline_args)

  @property
  def name(self):
    return 'Verilator'

  @property
  def backends(self):
    return ('verilog',)

  def verify(self, files, backend, top_entity):
    with tempfile.TemporaryDirectory() as tmp_path:
      sctx = self._make_subs_ctx(files, backend, top_entity)

      cmdline = re.split(r'\s+', string.Template(self.CMDLINE).substitute(**sctx))

      try:
        output = subprocess.check_output([self._xpath] + cmdline + list(files),
                                         stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as ex:
        pyu.fatal(f'Verification process exited with {ex.returncode} code. ' \
                  f'Error output:\n' + ex.output.decode())

      return output


class SlangVerifier(Verifier):

  BINARY = 'slang'
  CMDLINE = '-q --std 1800-2017 --top $TOP'

  def __init__(self, cmdline_args):
    super().__init__(self.BINARY, cmdline_args)

  @property
  def name(self):
    return 'Slang'

  @property
  def backends(self):
    return ('verilog',)

  def verify(self, files, backend, top_entity):
    with tempfile.TemporaryDirectory() as tmp_path:
      sctx = self._make_subs_ctx(files, backend, top_entity)

      cmdline = re.split(r'\s+', string.Template(self.CMDLINE).substitute(**sctx))

      try:
        output = subprocess.check_output([self._xpath] + cmdline + list(files),
                                         stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as ex:
        pyu.fatal(f'Verification process exited with {ex.returncode} code. ' \
                  f'Error output:\n' + ex.output.decode())

      return output


class YosysVerifier(Verifier):

  BINARY = 'yosys'
  CMDLINE = '-q -s'

  def __init__(self, cmdline_args):
    super().__init__(self.BINARY, cmdline_args)
    self._backends = ['verilog']
    self._plugins = []
    self._backend_read = {
      'verilog': ['read_verilog -sv $SFILES'],
    }
    self._find_plugins()

  def _check_plugin(self, name, search_paths):
    for path in search_paths:
      ppath = os.path.join(path, f'{name}.so')
      if os.path.exists(ppath):
        return ppath

  def _find_plugins(self):
    bin_path = os.path.dirname(self._xpath)
    search_paths = [
      bin_path,
      os.path.join(os.path.dirname(bin_path), 'lib'),
    ]
    if path := os.getenv('YOSYS_PLUGINS_PATH'):
      search_paths.append(os.path.abspath(path))

    alog.debug(f'Yosys Search Path: {search_paths}')

    if ppath := self._check_plugin('ghdl', search_paths):
      self._plugins.append(ppath)
      self._backends.append('vhdl')
      self._backend_read['vhdl'] = ['ghdl --std=08 $SFILES -e $TOP']

    if ppath := self._check_plugin('slang', search_paths):
      self._plugins.append(ppath)
      self._backend_read['verilog'] = [('read_slang --single-unit --allow-use-before-declare '
                                        '--allow-hierarchical-const --top $TOP $SFILES')]

  def _create_script(self, files, backend):
    script = list(self._backend_read[backend])

    script.append('hierarchy -check -top $TOP')
    script.append('check')
    script.append('synth')

    return '\n'.join(script)

  @property
  def name(self):
    return 'Yosys'

  @property
  def backends(self):
    return tuple(sorted(self._backends))

  def verify(self, files, backend, top_entity):
    with tempfile.TemporaryDirectory() as tmp_path:
      script = self._create_script(files, backend)

      sctx = self._make_subs_ctx(files, backend, top_entity)

      script = string.Template(script).substitute(**sctx)

      alog.debug(f'Yosys Script:\n{textwrap.indent(script, "  ")}')

      fd, path = tempfile.mkstemp(dir=tmp_path, suffix='.ys', text=True)
      with os.fdopen(fd, mode='wt') as tfd:
        tfd.write(script)

      cmdline = re.split(r'\s+', string.Template(self.CMDLINE).substitute(**sctx))

      plugins = []
      for mpath in self._plugins:
        plugins.extend(['-m', mpath])

      try:
        output = subprocess.check_output([self._xpath] + plugins + cmdline + [path],
                                         stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as ex:
        pyu.fatal(f'Verification process exited with {ex.returncode} code. ' \
                  f'Error output:\n' + ex.output.decode())

      return output


VERIFY_TOOLS = {
  # Ensure you have sourced the Vivado settings shell script which sets up the
  # proper environment variables (usually named settings64.sh).
  'Vivado': VivadoVerifier,
  'GHDL': GhdlVerifier,
  'Verilator': VerilatorVerifier,
  'Slang': SlangVerifier,
  'Yosys': YosysVerifier,
}

def _load_verifiers(args):
  verifiers, exclude = [], set(args.exclude or [])

  for name, vclass in VERIFY_TOOLS.items():
    if name.lower() not in exclude:
      try:
        verifier = vclass(args)

        if args.backend in verifier.backends:
          alog.info(f'Adding {verifier.name} verifier')
          verifiers.append(verifier)
      except NotImplementedError:
        pass

  return verifiers


def _main(args):
  verifiers = _load_verifiers(args)

  if not verifiers:
    pyu.fatal(f'Unable to find any valid HDL verification tools')

  for verifier in verifiers:
    alog.info(f'Running {verifier.name} verifier on {args.backend} files {args.inputs}')

    verifier.verify(args.inputs, args.backend.lower(), args.entity)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='VHDL/Verilog Code Verifier',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--inputs', nargs='+', required=True,
                      help='The input files to be analyzed')
  parser.add_argument('--entity', type=str, required=True,
                      help='The root entity name')
  parser.add_argument('--backend', type=str, default='vhdl',
                      choices={'vhdl', 'verilog'},
                      help='The backend to generate the code for')
  parser.add_argument('--exclude', action='append',
                      choices=set(t.lower() for t in VERIFY_TOOLS.keys()),
                      help='The list of verifiers to be excluded')

  app_main.main(parser, _main)

