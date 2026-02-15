import enum

import py_misc_utils.core_utils as pycu
import py_misc_utils.num_utils as pynu

import pyxhdl as X
from pyxhdl import xlib as XL

from . import clk_trigger


class AluOps(enum.IntEnum):
  ADD = 0
  SUB = enum.auto()
  MUL = enum.auto()
  DIV = enum.auto()
  SDIV = enum.auto()
  AND = enum.auto()
  OR = enum.auto()
  XOR = enum.auto()
  NOT = enum.auto()
  CMP = enum.auto()
  SHR = enum.auto()
  SHL = enum.auto()


class AluFlags(enum.IntEnum):
  ZERO = 0
  OVERFLOW = enum.auto()
  CARRY = enum.auto()
  SIGN = enum.auto()


class AluIfc(X.Interface):

  IFC = 'CLK, RST_N, OP, A_VALUE, B_VALUE, IN_VALID, =XOUT, =XOUT_HI, =FLAGS, =OUT_VALID'

  def __init__(self, clk, reset, *, width=8):
    super().__init__('ALU', width=width)
    self.mkfield('CLK', clk)
    self.mkfield('RST_N', reset)

    self.mkfield('OP', X.Uint(pycu.enum_bits(AluOps)))
    self.mkfield('A_VALUE', X.Uint(width))
    self.mkfield('B_VALUE', X.Uint(width))
    self.mkfield('IN_VALID', X.BIT)
    self.mkfield('XOUT', X.Uint(width))
    self.mkfield('XOUT_HI', X.Uint(width))
    self.mkfield('FLAGS', X.Bits(pycu.enum_max(AluFlags) + 1))
    self.mkfield('OUT_VALID', X.BIT)


class Alu(X.Entity):

  PORTS = f'*IFC:{__name__}.AluIfc.IFC'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    delay_count = X.mkreg(X.UINT8)
    delay_enable = X.mkreg(X.BIT)

    clk_trigger.ClkTrigger(CLK=IFC.CLK,
                           RST_N=IFC.RST_N,
                           COUNT=delay_count,
                           EN=delay_enable,
                           ACTIVE=IFC.OUT_VALID)

  @X.hdl_process(sens='+IFC.CLK')
  def run(self):
    wide_t = X.Uint(IFC.width + 1)
    xwide_t = X.Uint(2 * IFC.width)
    res_wide = X.mkwire(wide_t)
    res_xwide = X.mkwire(xwide_t)
    res = X.mkwire(IFC.XOUT.dtype)

    if IFC.RST_N != 1:
      delay_count = 0
      delay_enable = 0
    else:
      if IFC.IN_VALID == 1:
        delay_count = 0
        delay_enable = 1

        IFC.FLAGS = 0

        match IFC.OP:
          case AluOps.ADD:
            res_wide = XL.cast(IFC.A_VALUE, wide_t) + IFC.B_VALUE
            IFC.FLAGS[AluFlags.ZERO] = (res_wide == 0)
            IFC.FLAGS[AluFlags.CARRY] = res_wide[-1]
            IFC.FLAGS[AluFlags.SIGN] = res_wide[-2]
            IFC.FLAGS[AluFlags.OVERFLOW] = ((IFC.A_VALUE[-1] == IFC.B_VALUE[-1]) and
                                            (res_wide[-2] != IFC.A_VALUE[-1]))
            IFC.XOUT = res_wide

          case AluOps.SUB:
            res_wide = XL.cast(IFC.A_VALUE, wide_t) - IFC.B_VALUE
            IFC.FLAGS[AluFlags.ZERO] = (res_wide == 0)
            IFC.FLAGS[AluFlags.CARRY] = res_wide[-1]
            IFC.FLAGS[AluFlags.SIGN] = res_wide[-2]
            IFC.FLAGS[AluFlags.OVERFLOW] = ((IFC.A_VALUE[-1] != IFC.B_VALUE[-1]) and
                                            (res_wide[-2] != IFC.A_VALUE[-1]))
            IFC.XOUT = res_wide

          case AluOps.CMP:
            res_wide = XL.cast(IFC.A_VALUE, wide_t) - IFC.B_VALUE
            IFC.FLAGS[AluFlags.ZERO] = (res_wide == 0)
            IFC.FLAGS[AluFlags.CARRY] = res_wide[-1]
            IFC.FLAGS[AluFlags.SIGN] = res_wide[-2]
            IFC.FLAGS[AluFlags.OVERFLOW] = ((IFC.A_VALUE[-1] != IFC.B_VALUE[-1]) and
                                            (res_wide[-2] != IFC.A_VALUE[-1]))

          case AluOps.MUL:
            res_xwide = XL.cast(IFC.A_VALUE, xwide_t) * IFC.B_VALUE
            IFC.FLAGS[AluFlags.ZERO] = (res_xwide == 0)
            IFC.FLAGS[AluFlags.SIGN] = res_xwide[IFC.width - 1]
            IFC.FLAGS[AluFlags.OVERFLOW] = (res_xwide[IFC.width: ] != 0)
            IFC.XOUT = res_xwide[: IFC.width]
            IFC.XOUT_HI = res_xwide[IFC.width:]
            delay_count = 5

          case AluOps.DIV:
            res = IFC.A_VALUE / IFC.B_VALUE
            IFC.FLAGS[AluFlags.ZERO] = (res == 0)
            IFC.FLAGS[AluFlags.SIGN] = res[-1]
            IFC.XOUT = res
            delay_count = 10

          case AluOps.SDIV:
            res = XL.cast(IFC.A_VALUE, X.Sint(IFC.width)) / XL.cast(IFC.B_VALUE, X.Sint(IFC.width))
            IFC.FLAGS[AluFlags.ZERO] = (res == 0)
            IFC.FLAGS[AluFlags.SIGN] = res[-1]
            IFC.XOUT = res
            delay_count = 10

          case AluOps.AND:
            res = IFC.A_VALUE & IFC.B_VALUE
            IFC.FLAGS[AluFlags.ZERO] = (res == 0)
            IFC.FLAGS[AluFlags.SIGN] = res[-1]
            IFC.XOUT = res

          case AluOps.OR:
            res = IFC.A_VALUE | IFC.B_VALUE
            IFC.FLAGS[AluFlags.ZERO] = (res == 0)
            IFC.FLAGS[AluFlags.SIGN] = res[-1]
            IFC.XOUT = res

          case AluOps.XOR:
            res = IFC.A_VALUE ^ IFC.B_VALUE
            IFC.FLAGS[AluFlags.ZERO] = (res == 0)
            IFC.FLAGS[AluFlags.SIGN] = res[-1]
            IFC.XOUT = res

          case AluOps.NOT:
            res = ~IFC.A_VALUE
            IFC.FLAGS[AluFlags.ZERO] = (res == 0)
            IFC.FLAGS[AluFlags.SIGN] = res[-1]
            IFC.XOUT = res

          case AluOps.SHR:
            res = IFC.A_VALUE >> IFC.B_VALUE
            IFC.FLAGS[AluFlags.ZERO] = (res == 0)
            IFC.FLAGS[AluFlags.SIGN] = res[-1]
            IFC.XOUT = res

          case AluOps.SHL:
            res = IFC.A_VALUE << IFC.B_VALUE
            IFC.FLAGS[AluFlags.ZERO] = (res == 0)
            IFC.FLAGS[AluFlags.SIGN] = res[-1]
            IFC.XOUT = res

          case _:
            pass

      else:
        delay_count = 0
        delay_enable = 0


class Test(X.Entity):

  ARGS = dict(clock_frequency=100e6,
              num_tests=20,
              width=8) | Alu.ARGS

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def root(self):
    from . import clock

    CLK = X.mkreg(X.BIT)

    clock.Clock(CLK=CLK,
                frequency=clock_frequency)

    RST_N = X.mkreg(X.BIT)

    self.ifc = AluIfc(CLK, RST_N,
                      width=width)

    Alu(IFC=self.ifc,
        **{k: locals()[k] for k in Alu.ARGS.keys()})

  @X.hdl_process()
  def init(self):
    import random

    from pyxhdl import xlib as XL
    from pyxhdl import testbench as TB

    def vstr(v, n):
      sv = pynu.sign_extend(v, n)
      return f'{v} ({sv})' if sv < 0 else f'{sv}'


    RST_N = 0
    self.ifc.IN_VALID = 0

    TB.wait_rising(CLK)

    RST_N = 1

    value_mask = 2**width - 1

    for i in range(num_tests):
      op = random.randint(0, pycu.enum_max(AluOps))
      a_value = random.randint(0, value_mask)
      if op in (AluOps.DIV, AluOps.SDIV):
        b_value = random.randint(1, value_mask)
      elif op in (AluOps.SHR, AluOps.SHL):
        b_value = random.randint(0, width)
      else:
        b_value = random.randint(0, value_mask)

      self.ifc.OP = op
      self.ifc.A_VALUE = a_value
      self.ifc.B_VALUE = b_value
      self.ifc.IN_VALID = 1

      TB.wait_until(CLK, self.ifc.OUT_VALID == 1)

      match op:
        case AluOps.ADD:
          result = a_value + b_value

        case AluOps.SUB:
          result = a_value - b_value

        case AluOps.CMP:
          result = None

        case AluOps.MUL:
          result = a_value * b_value

        case AluOps.DIV:
          result = int(a_value / b_value)

        case AluOps.SDIV:
          a_value = pynu.sign_extend(a_value, width)
          b_value = pynu.sign_extend(b_value, width)
          result = int(a_value / b_value)

        case AluOps.AND:
          result = a_value & b_value

        case AluOps.OR:
          result = a_value | b_value

        case AluOps.XOR:
          result = a_value ^ b_value

        case AluOps.NOT:
          result = ~a_value

        case AluOps.SHR:
          result = a_value >> b_value

        case AluOps.SHL:
          result = a_value << b_value

        case _:
          result = None

      if result is not None:
        mresult = result & value_mask
        avs, bvs, rvs = [vstr(x, width) for x in (a_value, b_value, mresult)]

        TB.compare_value(self.ifc.XOUT, mresult,
                         msg=f' : op={AluOps(op).name}, a={avs}, b={bvs}, res={rvs}')

      self.ifc.IN_VALID = 0
      TB.wait_rising(CLK)

    XL.finish()

