import argparse
import collections
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import textwrap

import py_misc_utils.alog as alog
import py_misc_utils.app_main as app_main
import py_misc_utils.fs_utils as pyfsu
import py_misc_utils.template_replace as pytr
import py_misc_utils.utils as pyu


class Tester:

  def __init__(self, cmdline_args):
    if isinstance(self.BINARY, (list, tuple)):
      xpath = dict()
      for binary in self.BINARY:
        bpath = shutil.which(binary)
        if not bpath:
          alog.debug(f'Unable to find binary "{binary}" for {self.NAME} tester')
          raise NotImplementedError(f'Unable to find binary "{binary}" for {self.NAME} tester')

        xpath[binary] = bpath
    else:
      xpath = shutil.which(self.BINARY)
      if not xpath:
        alog.debug(f'Unable to find binary "{self.BINARY}" for {self.NAME} tester')
        raise NotImplementedError(f'Unable to find binary "{self.BINARY}" for {self.NAME} tester')

    alog.info(f'Found {self.NAME} tester at {xpath}')

    self._xpath = xpath
    self._args = cmdline_args
    self._binary_args = getattr(cmdline_args, f'{self.NAME}_args', None) or []

  def _prepare_cmdline_ctx(self, source_file, backend, top_entity, **kwargs):
    sctx = {
      'INPUT': source_file,
      'TOP': top_entity,
      'BACKEND': backend,
      'ARGS': ' '.join(self._binary_args),
    }
    sctx.update(kwargs)

    return sctx

  def _expand_cmdline(self, cmdline, sctx):
    cmdstr = pytr.template_replace(cmdline, lookup_fn=pytr.defval_lookup(sctx, ''))

    return shlex.split(cmdstr)

  def _get_vcd_path(self, source_file):
    if self._args.vcdpath:
      test_name, ext = os.path.splitext(os.path.basename(source_file))

      return os.path.join(self._args.vcdpath, f'{test_name}_{self.NAME}_{ext[1: ]}.vcd')

  @classmethod
  def add_args(cls, parser):
    parser.add_argument(f'--{cls.NAME}_args', nargs='+', action='extend',
                        help=f'The arguments for the {cls.NAME} tester')


class GhdlTester(Tester):

  NAME = 'ghdl'
  BINARY = 'ghdl'
  CMDLINE = '-c --std=08 --workdir=$WORKDIR -frelaxed -Wno-shared $ARGS $INPUT -r $TOP $VCD'

  @property
  def backends(self):
    return ('vhdl',)

  def _parse_vcd_args(self, sctx):
    if vcd_path := self._get_vcd_path(sctx['INPUT']):
      sctx['VCD'] = f'--vcd={vcd_path}'

    return sctx

  def test(self, source_file, backend, top_entity):
    with tempfile.TemporaryDirectory() as tmp_path:
      sctx = self._prepare_cmdline_ctx(source_file, backend, top_entity,
                                       WORKDIR=tmp_path)

      sctx = self._parse_vcd_args(sctx)

      cmdline = [self._xpath] + self._expand_cmdline(self.CMDLINE, sctx)

      alog.debug(f'Running GHDL Tester: {cmdline}')
      try:
        output = subprocess.check_output(cmdline, stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as ex:
        pyu.fatal(f'Test process exited with {ex.returncode} code: {cmdline}\n' \
                  f'Error output:\n' + ex.output.decode())

      return output


class VerilatorTester(Tester):

  NAME = 'verilator'
  BINARY = 'verilator'
  CMDLINE = '--binary --timing --trace --assert -sv --Mdir $WORKDIR $ARGS -o VTest --top $TOP $INPUT $VCD'

  @property
  def backends(self):
    return ('verilog',)

  def _create_dumper_module(self, tmp_path, vcd_path, top_entity, modname):
    template = """
      module $MODNAME;
        $TOP umod();
        initial begin
          $$dumpfile("$VCDPATH");
          $$dumpvars();
        end
      endmodule
    """

    vals = dict(MODNAME=modname, TOP=top_entity, VCDPATH=vcd_path)

    code = pytr.template_replace(template, lookup_fn=pytr.defval_lookup(vals, ''))
    dcode = textwrap.dedent(code)

    mod_path = os.path.join(tmp_path, 'vcd_dumper.sv')
    with open(mod_path, mode='w') as fd:
      fd.write(dcode)

    return mod_path

  def _parse_vcd_args(self, sctx):
    if vcd_path := self._get_vcd_path(sctx['INPUT']):
      modname = sctx['TOP'] + '_VCD'
      mod_path = self._create_dumper_module(sctx['WORKDIR'], vcd_path, sctx['TOP'],
                                            modname)

      sctx['VCD'] = f'--trace-vcd {mod_path}'
      sctx['TOP'] = modname

    return sctx

  def test(self, source_file, backend, top_entity):
    with tempfile.TemporaryDirectory() as tmp_path:
      sctx = self._prepare_cmdline_ctx(source_file, backend, top_entity,
                                       WORKDIR=tmp_path)

      sctx = self._parse_vcd_args(sctx)

      gen_cmdline = [self._xpath] + self._expand_cmdline(self.CMDLINE, sctx)

      alog.debug(f'Running Verilator Tester: {gen_cmdline}')
      try:
        gen_output = subprocess.check_output(gen_cmdline, stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as ex:
        pyu.fatal(f'Test process exited with {ex.returncode} code: {gen_cmdline}\n' \
                  f'Error output:\n' + ex.output.decode())

      run_cmdline = [os.path.join(tmp_path, 'VTest')]
      try:
        run_output = subprocess.check_output(run_cmdline, stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as ex:
        pyu.fatal(f'Test process exited with {ex.returncode} code: {run_cmdline}\n' \
                  f'Error output:\n' + ex.output.decode())

      return gen_output + run_output


class VivadoTester(Tester):

  NAME = 'vivado'
  CMDLINE = {
    'xvlog': '$XVLOG_ARGS -sv $INPUT',
    'xvhdl': '$XVHDL_ARGS -2008 $INPUT',
    'xelab': '$XELAB_ARGS -debug wave $TOP',
    'xsim': '$XSIM_ARGS -onerror quit -t $TCL_SCRIPT $TOP',
  }
  BINARY = tuple(CMDLINE.keys())

  @property
  def backends(self):
    return ('verilog', 'vhdl')

  def _select_args(self, binary):
    for arg in self._binary_args:
      if m := re.match(rf'{binary}:(.*)'):
        yield m.group(1)

  def _create_tcl_script(self, sctx):
    # We need to insert a catch{} within the script, otherwise if there is some
    # error in the script, the simulation hangs since xsim drops to an interactive
    # shell (even though we pass the '-onerror quit' command line argument).
    template = """
    proc testbench {} {
      if { [ info exists ::env(VCDPATH)] } {
        open_vcd $$::env(VCDPATH)
        log_vcd /$$::env(TOP)/*
      }
      run all
      exit
    }

    if { [ catch { testbench } ERRMSG ] } {
      puts stderr "TCL_SCRIPT: $$ERRMSG"
      exit 1
    }
    """

    if vcd_path := self._get_vcd_path(sctx['INPUT']):
      sctx['VCDPATH'] = vcd_path

    script = pytr.template_replace(template, lookup_fn=pytr.defval_lookup(sctx, ''))
    dscript = textwrap.dedent(script)

    script_path = os.path.join(sctx['WORKDIR'], 'xsim.tcl')
    with open(script_path, mode='w') as fd:
      fd.write(dscript)

    sctx['TCL_SCRIPT'] = script_path

    return sctx

  def _parse_args(self, sctx):
    sctx = self._create_tcl_script(sctx)

    for binary in self.BINARY:
      sctx[f'{binary.upper()}_ARGS'] = ' '.join(self._select_args(binary))

    return sctx

  def test(self, source_file, backend, top_entity):
    with (tempfile.TemporaryDirectory() as tmp_path, pyfsu.cwd(tmp_path)):
      sctx = self._prepare_cmdline_ctx(source_file, backend, top_entity,
                                       WORKDIR=tmp_path)

      sctx = self._parse_args(sctx)

      proc_tool = {
        'verilog': 'xvlog',
        'vhdl': 'xvhdl',
      }[backend]

      proc_cmdline = [self._xpath[proc_tool],
                      *self._expand_cmdline(self.CMDLINE[proc_tool], sctx)]

      alog.debug(f'Running Vivado Tester (Processing): {proc_cmdline}')
      try:
        proc_output = subprocess.check_output(proc_cmdline, stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as ex:
        pyu.fatal(f'Test process exited with {ex.returncode} code: {proc_cmdline}\n' \
                  f'Error output:\n' + ex.output.decode())

      elab_cmdline = [self._xpath['xelab'],
                      *self._expand_cmdline(self.CMDLINE['xelab'], sctx)]

      alog.debug(f'Running Vivado Tester (Elaboration): {elab_cmdline}')
      try:
        elab_output = subprocess.check_output(elab_cmdline, stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as ex:
        pyu.fatal(f'Test process exited with {ex.returncode} code: {elab_cmdline}\n' \
                  f'Error output:\n' + ex.output.decode())

      run_cmdline = [self._xpath['xsim'],
                     *self._expand_cmdline(self.CMDLINE['xsim'], sctx)]

      alog.debug(f'Running Vivado Tester: {run_cmdline}')
      try:
        # The TCL script gets its arguments from the environment (no way to pass
        # them to the xsim command line ATM), so we need to create an updated copy
        # of the current environment.
        env = os.environ.copy()
        env.update(sctx)

        run_output = subprocess.check_output(run_cmdline,
                                             stderr=subprocess.STDOUT,
                                             env=env)
      except subprocess.CalledProcessError as ex:
        pyu.fatal(f'Test process exited with {ex.returncode} code: {run_cmdline}\n' \
                  f'Error output:\n' + ex.output.decode())

      return proc_output + elab_output + run_output


TEST_TOOLS = {
  'GHDL': GhdlTester,
  'Verilator': VerilatorTester,
  'Vivado': VivadoTester,
}

def add_tests_args(parser):
  for tclass in TEST_TOOLS.values():
    tclass.add_args(parser)


def load_testers(args):
  testers = []

  for name, tclass in TEST_TOOLS.items():
    try:
      tester = tclass(args)

      alog.info(f'Adding {tester.NAME} tester')
      testers.append(tester)
    except NotImplementedError:
      pass

  return testers


GenCode = collections.namedtuple('GenCode', 'input, output, backend, entity')

def generate_code(source_file, args, output_path):
  test_name, _ = os.path.splitext(os.path.basename(source_file))

  backends = re.split(r'\s*,\s*', args.backend)

  python_path = shutil.which('python') or shutil.which('python3')

  code = []
  for backend in backends:
    output_file = os.path.join(output_path, f'{test_name}.{backend}')
    cmdline = [
      python_path,
      '-m', 'pyxhdl.generator',
      '--backend', backend,
      '--input_file', source_file,
      '--output_file', output_file,
      '--entity', args.entity,
      '--log_level', args.log_level,
    ]

    for arg in args.gargs or []:
      cmdline.extend(pyu.comma_split(arg))

    test_args = list(args.args) if args.args else []
    if env_args := os.getenv(f'{test_name.upper()}_UTARGS'):
      test_args.extend(pyu.comma_split(env_args))

    if test_args:
      cmdline.append('--kwargs')
      cmdline.extend(test_args)

    alog.debug(f'Running Code Generator: {cmdline}')
    try:
      output = subprocess.check_output(cmdline, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
      pyu.fatal(f'Generation process exited with {ex.returncode} code: {cmdline}\n' \
                f'Error output:\n' + ex.output.decode())

    code.append(GenCode(source_file, output_file, backend, args.entity))

  return code


def filter_errors(soutput):
  lines = []
  for line in soutput.split('\n'):
    m = re.match(r'ERR:\s+\d+\s+', line)
    if m:
      lines.append(line)

  return lines


def main(args):
  testers = load_testers(args)

  if not testers:
    pyu.fatal(f'Unable to find any valid HDL test tools')

  with tempfile.TemporaryDirectory() as tmp_path:
    code = []
    for source_file in args.inputs:
      code.extend(generate_code(os.path.abspath(source_file), args, tmp_path))

    failed = []
    for tester in testers:
      for gcode in code:
        if gcode.backend in tester.backends:
          alog.info(f'Running {tester.NAME} tester on {gcode.backend} file {gcode.output}')

          output = tester.test(gcode.output, gcode.backend, gcode.entity)

          soutput = output.decode()
          alog.debug(soutput)

          mmlines = filter_errors(soutput)
          if mmlines:
            failed.append((gcode, tester.NAME, mmlines))

    if failed:
      for gcode, tname, lines in failed:
        elines = '    ' + '\n    '.join(lines)
        alog.error(f'Failed test for {tname} tool: source={gcode.input} backend={gcode.backend}\n{elines}')

      sys.exit(1)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='PyXHDL Unit Tester',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--inputs', nargs='+', action='extend', required=True,
                      help='The PyXHDL input files to be tested')
  parser.add_argument('--entity', type=str, default='Test',
                      help='The root entity name')
  parser.add_argument('--backend', type=str, default='verilog,vhdl',
                      help='The backends to test for')
  parser.add_argument('--gargs', nargs='+', action='extend',
                      help='The code generator extra arguments')
  parser.add_argument('--args', nargs='+', action='extend',
                      help='The code generator input keyword arguments with NAME=VALUE format')
  parser.add_argument('--vcdpath',
                      help='The patch of the VCD trace file')

  add_tests_args(parser)

  app_main.main(parser, main)

