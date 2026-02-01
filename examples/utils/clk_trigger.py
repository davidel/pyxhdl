import random

import pyxhdl as X
from pyxhdl import xlib as XL


class ClkTrigger(X.Entity):

  PORTS = 'CLK=bit, RST_N=bit, COUNT, EN=bit, =ACTIVE=bit'

  @X.hdl_process(sens='+CLK')
  def run(self):
    enabled = X.mkreg(X.BIT)
    trigger_count = X.mkreg(COUNT.dtype)
    counter = X.mkreg(COUNT.dtype)

    if RST_N != 1:
      ACTIVE = 0
      enabled = 0
      trigger_count = 0
      counter = 0
    else:
      if not EN:
        enabled = 0
        ACTIVE = 0
      elif enabled:
        if not ACTIVE:
          if counter + 1 == trigger_count:
            ACTIVE = 1
          else:
            counter += 1
      else:
        trigger_count = COUNT
        counter = 0
        enabled = 1
        if COUNT == 0:
          ACTIVE = 1


class Test(X.Entity):

  ARGS = dict(clock_frequency=100e6, num_tests=10) | ClkTrigger.ARGS

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    from . import clock

    CLK = X.mkreg(X.BIT)

    clock.Clock(CLK=CLK,
                frequency=clock_frequency)

    RST_N = X.mkreg(X.BIT)
    COUNT = X.mkreg(X.UINT8)
    EN = X.mkreg(X.BIT)
    ACTIVE = X.mkreg(X.BIT)

    ClkTrigger(CLK=CLK,
               RST_N=RST_N,
               COUNT=COUNT,
               EN=EN,
               ACTIVE=ACTIVE,
               **{k: locals()[k] for k in ClkTrigger.ARGS.keys()})

  @X.hdl_process()
  def init(self):
    from pyxhdl import testbench as TB

    RST_N = 0
    EN = 0
    COUNT = 0

    TB.wait_rising(CLK)

    RST_N = 1

    for i in range(num_tests):
      counter = random.randint(0, 10)

      COUNT = counter
      EN = 1

      for _ in range(counter + 1):
        TB.wait_rising(CLK)

      TB.compare_value(ACTIVE, 1)

      EN = 0
      TB.wait_rising(CLK)

    XL.finish()

