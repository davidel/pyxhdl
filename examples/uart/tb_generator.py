import random

import pyxhdl as X
from pyxhdl import xlib as XL
from pyxhdl import testbench as TB

class UartData:

  def __init__(self, eclass, inputs, args,
                clocks=None,
                **kwargs):
    assert clocks, 'Missing clocks definitions'

    self.eclass = eclass
    self.inputs = inputs
    self.arg = args
    self.clk = clocks[0]
    self.input_fields = ('RST_N', 'UIN', 'CTS')
    self.output_fields = ('UOUT', 'RTS')
    self.baud_rate = inputs.get('baud_rate', 115200)
    self.bit_time = 1.0 / self.baud_rate
    self.num_tests = inputs.get('num_tests', 20)
    self.env = dict()

  def emit(self, wait=None, **kwargs):
    inputs = {name: kwargs[name] for name in self.input_fields if name in kwargs}
    outputs = {name: kwargs[name] for name in self.output_fields if name in kwargs}

    return TB.TbData(inputs=inputs,
                     outputs=outputs,
                     wait=self.bit_time if wait is None else wait,
                     wait_expr=None,
                     env=self.env)

  def wait(self, wait_expr):
    return TB.TbData(inputs=dict(),
                     outputs=dict(),
                     wait=None,
                     wait_expr=wait_expr,
                     env=self.env)

  def _gen_byte(self, value):
    yield self.emit(UIN=0)

    cvalue = value
    for i in range(8):
      yield self.emit(UIN=cvalue & 1)
      cvalue = cvalue >> 1

    yield self.emit(wait=self.bit_time / 2, UIN=1)

  def _match_byte(self, value):
    yield self.wait('XL.wait_until(UOUT == 0)')
    yield self.emit(wait=self.bit_time / 2, UOUT=0)

    cvalue = value
    for i in range(8):
      yield self.emit(UOUT=cvalue & 1)
      cvalue = cvalue >> 1

    yield self.emit(UOUT=1)

  def generate(self):
    yield self.emit(RST_N=0)
    yield self.emit(RST_N=1, UIN=1)

    for i in range(self.num_tests):
      value = random.randint(0, 255)

      XL.write(f'{{NOW}} [{i}] value={value:08b} ({value})')

      yield from self._gen_byte(value)
      yield from self._match_byte(value)


def tb_iterator(eclass, inputs, args,
                clocks=None,
                **kwargs):
  udata = UartData(eclass, inputs, args, clocks=clocks, **kwargs)

  return iter(udata.generate())

