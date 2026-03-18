import argparse
import collections
import os
import re
import shutil
import string
import subprocess
import tempfile

import py_misc_utils.alog as alog
import py_misc_utils.app_main as app_main
import py_misc_utils.utils as pyu


class Tester:

  def __init__(self, binary, cmdline_args):
    xpath = shutil.which(binary)
    if not xpath:
      alog.debug(f'Unable to find binary "{binary}" for {self.name} tester')
      raise NotImplementedError(f'Unable to find binary "{binary}" for {self.name} tester')

    alog.info(f'Found {self.name} tester at {xpath}')

    self._binary = binary
    self._xpath = xpath
    self._args = cmdline_args

  def _make_subs_ctx(self, source_file, backend, top_entity, **kwargs):
    sctx = {
      'INPUT': source_file,
      'TOP': top_entity,
      'BACKEND': backend,
    }
    sctx.update(kwargs)

    return sctx


class GhdlTester(Tester):

  BINARY = 'ghdl'
  CMDLINE = '-c --std=08 --workdir=$WORKDIR -frelaxed -Wno-shared $INPUT -r $TOP'

  def __init__(self, cmdline_args):
    super().__init__(self.BINARY, cmdline_args)

  @property
  def name(self):
    return 'GHDL'

  @property
  def backends(self):
    return ('vhdl',)

  def test(self, source_file, backend, top_entity):
    with tempfile.TemporaryDirectory() as tmp_path:
      sctx = self._make_subs_ctx(source_file, backend, top_entity,
                                 WORKDIR=tmp_path)

      cmdline = [self._xpath] + re.split(r'\s+', string.Template(self.CMDLINE).substitute(**sctx))
      try:
        output = subprocess.check_output(cmdline, stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as ex:
        pyu.fatal(f'Test process exited with {ex.returncode} code: {cmdline}\n' \
                  f'Error output:\n' + ex.output.decode())

      return output


class VerilatorTester(Tester):

  BINARY = 'verilator'
  CMDLINE = '--binary --timing --trace --assert -sv --Mdir $WORKDIR -o VTest --top-module $TOP $INPUT'

  def __init__(self, cmdline_args):
    super().__init__(self.BINARY, cmdline_args)

  @property
  def name(self):
    return 'Verilator'

  @property
  def backends(self):
    return ('verilog',)

  def test(self, source_file, backend, top_entity):
    with tempfile.TemporaryDirectory() as tmp_path:
      sctx = self._make_subs_ctx(source_file, backend, top_entity,
                                 WORKDIR=tmp_path)

      cmdline = [self._xpath] + re.split(r'\s+', string.Template(self.CMDLINE).substitute(**sctx))
      try:
        gen_output = subprocess.check_output(cmdline, stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as ex:
        pyu.fatal(f'Test process exited with {ex.returncode} code: {cmdline}\n' \
                  f'Error output:\n' + ex.output.decode())

      cmdline = [os.path.join(tmp_path, 'VTest')]
      try:
        run_output = subprocess.check_output(cmdline, stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as ex:
        pyu.fatal(f'Test process exited with {ex.returncode} code: {cmdline}\n' \
                  f'Error output:\n' + ex.output.decode())

      return gen_output + run_output


TEST_TOOLS = {
  'GHDL': GhdlTester,
  'Verilator': VerilatorTester,
}

def load_testers(args):
  testers = []

  for name, tclass in TEST_TOOLS.items():
    try:
      tester = tclass(args)

      alog.info(f'Adding {tester.name} tester')
      testers.append(tester)
    except NotImplementedError:
      pass

  return testers


GenCode = collections.namedtuple('GenCode', 'input, output, backend')

def generate_code(source_file, args, ouput_path):
  test_name, _ = os.path.splitext(os.path.basename(source_file))

  backends = re.split(r'\s*,\s*', args.backend)

  code = []
  for backend in backends:
    output_file = os.path.join(ouput_path, f'{test_name}.{backend}')
    cmdline = [
      'python',
      '-m', 'pyxhdl.generator',
      '--backend', backend,
      '--input_file', source_file,
      '--output_file', output_file,
      '--entity', args.entity,
      '--log_level', args.log_level,
    ]
    for arg in args.args or ():
      cmdline.extend(['--kwargs', arg])

    try:
      output = subprocess.check_output(cmdline, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
      pyu.fatal(f'Generation process exited with {ex.returncode} code: {cmdline}\n' \
                f'Error output:\n' + ex.output.decode())

    code.append(GenCode(source_file, output_file, backend))

  return code


def main(args):
  testers = load_testers(args)

  if not testers:
    pyu.fatal(f'Unable to find any valid HDL test tools')

  with tempfile.TemporaryDirectory() as tmp_path:
    code = []
    for source_file in args.inputs:
      code.extend(generate_code(source_file, args, tmp_path))

    for tester in testers:
      for gcode in code:
        if gcode.backend in tester.backends:
          alog.info(f'Running {tester.name} tester on {gcode.backend} file {gcode.output}')

          output = tester.test(gcode.output, gcode.backend, args.entity)

          alog.debug(output.decode())


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='PyXHDL Unit Tester',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--inputs', nargs='+', required=True,
                      help='The PyXHDL input files to be tested')
  parser.add_argument('--entity', type=str, default='Test',
                      help='The root entity name')
  parser.add_argument('--backend', type=str, default='verilog,vhdl',
                      help='The backends to test for')
  parser.add_argument('--args', nargs='+',
                      help='The input arguments with NAME=VALUE format')

  app_main.main(parser, main)

