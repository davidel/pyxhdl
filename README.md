# PyXHDL - Python Frontend For VHDL And Verilog

*PyXHDL* born for developers who are not really in love with any of the HDL languages
and instead appreciate the simplicity and flexibility of using Python for their workflows.


## Install

The easiest way to install *PyXHDL* is using PIP from the direct Github repo.

```Shell
$ pip install git+https://github.com/davidel/pyxhdl.git
```


## Description

*PyXHDL* allows to write HDL code in Python, generating VHDL (2008) and Verilog
(SystemVerilog) code to be used for synthesis and simulation.

*PyXHDL* does not try to create an IR to be lowered, but instead interprets Python AST
code and maps that directly into the selected HDL backend code. The optimizations are
left to the OEM HDL compiler used to syntesize the design.

Even though user HDL code in Python can use loops and functions, everything will be unrolled
in the final VHDL/Verilog code (this is what the synthesis will do anyway, since there are
no loops or function calls in HW).

*PyXHDL* does not try to map Python loops to VHDL/Verilog ones, as those are too limited
when compared to the power of the Python ones, but instead unrolls them like the OEM HDL
compiler will.

The workflow with *PyXHDL* is not meant as to generate code to be manually edited, but
to be directly fed into OEM HDL synthesis (and testing, when using the *testbench* code
generation) tools.

An *IF* statement in Python gets emitted as *IF* of the target HDL language, if the test
depends on HDL variables (the *X.Value* type), or gets statically resolved to the if/else
branch like it normally would in Python.

Note that in case the *IF* test condition depends on HDL variables, both branches are
executed in order to generate the proper HDL code. See the following code for the
*pyint* pitfall.

```Python
pyint = 0
if hdlvar > 2:
  # IF HDL code
  ...
  pyint += 1
else:
  # ELSE HDL code
  ...
  pyint += 1

# pyint == 2 here!
```

On the contrary, *IF* statements whose condition only depends on Python variables,
is resolved statically and the "false branch" never executed/emitted.

```Python
if pyint > 2:
  hdl_var1 = hdl_var2 + 17
else:
  hdl_array[2, 1] = hdl_array[1, 2]
```

In the above example if, say, *pyint* is 3, the *ELSE* branch won't be evaluated,
which means that no code will be emitted for the HDL array operation in it.

If an HDL function contains return statements nested within a branch depending on
the value of an HDL variable, all the "return paths" must have the same signature.

Below, if *hdl_var1* is *X.Bits(5)* and *hdl_var2* is *X.Bits(8)*, the function
is valid because both return paths return a two-element tuple with signature
*X.Bits(11)*, *X.Bits(8)* (*PyXHDL* borrowed the Python _MatMul_ operator "@" for
bits concatenation).

```Python
@X.hdl
def tuple_return(hdl_var1, hdl_var2):
  if hdl_var1 == "0b01101":
    return hdl_var1 @ "0b110110", hdl_var2
  ...
  return hdl_var2 @ "0b101", hdl_var1 @ "0b001"
```

The normal Python *FOR* and *WHILE* loops are supported in full, but the generators and
tests should not depend on HDL code (IOW the loop has to be deterministic, as required
by synthesis).

Within Python loops, it is not possible to have *BREAK* and *CONTINUE* within a branch
(*IF*) that depends on an HDL variable. Even this case behavior is dictated by the
fact that *PyXHDL* emitted code must be synthesisazible (deterministic loops).
So this is not possible:

```Python
for i, hdl_value in enumerate(my_hdl_generator(...)):
  ...
  if hdl_value == 0:
    break
```

While this is (assuming *max_count* a Python scalar):

```Python
for i, hdl_value in enumerate(my_hdl_generator(...)):
  ...
  if i > max_count:
    break
```

The data access model of VHDL and Verilog differs quite a bit from a user level
POV (though it converges at the end at lower level).

In VHDL it is not possible (modulo declaring them *shared* which is usually a bad
idea) to have global registers (entity level variables), while it is possible to
assign wires (signals) from within processes.

On the contrary in Verilog it is possible to declare registers at module level
(though only one process can write them), but it is not possible to assign wires
from within processes (*always* blocks of kind).

In *PyXHDL* wires are emitted as declared at module level, and it is allowed to
write them from within HDL processes (the *X.hdl_process()* Python methods of
the user *X.Entity* instantiations). This follows the VHDL pattern, which is resolved
in Verilog by creating a global (module level) register collecting the write
operations, and then continuosly assigned to the wire at global level.

For example, the following *PyXHDL* code:

```Python
class Ex1(X.Entity):

  PORTS = 'CLK, A, B, =XOUT'

  @X.hdl_process(sens='+CLK')
  def run():
    XOUT = A + B
```

Will generate the following VHDL and Verilog outputs (which in turn generate the
same RTL when fed to OEM synthesis tools):

```VHDL
architecture behavior of Ex1 is
begin
  run : process (CLK)
  begin
    if rising_edge(CLK) then
      XOUT <= A + B;
    end if;
  end process;
end architecture;
```

```Verilog
module Ex1(CLK, A, B, XOUT);
  input logic CLK;
  input logic [7: 0] A;
  input logic [7: 0] B;
  output logic [7: 0] XOUT;
  logic [7: 0] XOUT_;
  always @(posedge CLK)
  begin
    XOUT_ <= A + B;
  end
  assign XOUT = XOUT_;
endmodule
```

HDL variables should be declared before being assigned. An assignment to a bare Python
variable with the result of an HDL operation, will simply create the *X.Value* result
and store it to the Python variable, no HDL assignment will be generated.

Example:

```Python
wtemp = X.mkreg(hdl_var1.dtype)
temp = hdl_var1 + hdl_var2
wtemp = hdl_var1 - hdl_var2
# Somewhere below the "temp" value will be used ...
```

In the above code, an HDL assignment to the *wtemp* HDL variable will be generated,
while the *temp* assignment won't generate one (it can be seen as temporary value to
be used in following computations).

When an HDL variable is declared of a given type, assignments to it will cast the RHS
to the type of the variable.

```Python
C = X.mkreg(X.Bits(10))

# If A is Bits(4) and B is Bits(8), C will be (as declared) Bits(10) obtained by truncating
# the concatenation result of Bits(12).
C = A @ B
```

Python functions which contains operations on *X.Value* types need to be marked with the
*@X.hdl* decorator, while *X.Entity* methods which are to be translated to processes,
need to be marked with the *@X.hdl_process* decorator.

Note that if a Python function simply handles HDL variables as data, or uses their object
APIs, there is no need to decorate the functions as HDL. So this is valid from a *PyXHDL*
point of view:

```Python
def hdl_handler(hdl_v1, hdl_v2):
  assert hdl_v1.dtype == hdl_v2.dtype, f'Types must match: {hdl_v1.dtype} vs. {hdl_v2.dtype}'

  return dict(v1=hdl_v1, v2=hdl_v2), (hdl_v1, hdl_v2)
```

The Python matrix multiplication operator "@" has been repurposed to mean concatenation
of bits sequences.


## Data Types

The types supported by *PyXHDL* are *Uint* (unsigned integer), *Sint* (signed integer),
*Bits* (generic bit group), *Float* (HW synthesizable floating point), *Integer* (generic
integer), *Real* (generic floating point) and *Bool* (boolean).

```Python
# A 8 bits unsigned integer type.
u8 = X.Uint(8)
# A 15 bits signed integer type.
s15 = X.Sint(15)
# A 32 bits group type.
b32 = X.Bits(32)
# A 32 bits floating point type.
f32 = X.Float(32)
```

The following types are predefined for an easy use.

```Python
INT4 = Sint(4)
INT8 = Sint(8)
INT16 = Sint(16)
INT32 = Sint(32)
INT64 = Sint(64)
INT128 = Sint(128)

UINT4 = Uint(4)
UINT8 = Uint(8)
UINT16 = Uint(16)
UINT32 = Uint(32)
UINT64 = Uint(64)
UINT128 = Uint(128)

FLOAT16 = Float(16)
FLOAT32 = Float(32)
FLOAT64 = Float(64)
FLOAT80 = Float(80)
FLOAT128 = Float(128)

BOOL = Bool()
BIT = Bits(1)
INT = Integer()
REAL = Real()
VOID = Void()
```

In order for the HW synthesizable floating point to be fully specified, a mapping
from the full number of bits representation to the exponent and mantissa size is
required.

The default mapping is the following, which follows the IEEE standard.

```Python
# FSpec = FSpec(EXP_SIZE, MANT_SIZE)
_FLOAT_SPECS = {
  16: FSpec(5, 10),
  32: FSpec(8, 23),
  64: FSpec(11, 52),
  80: FSpec(17, 63),
  128: FSpec(15, 112),
}
```

It is possible to override that using a configuration file or defining environment
variables. Example, define the *F16_SPEC* environment varible to "8,7" to map the
16 bits floating point number to the *BFLOAT16* standard.

While VHDL (2008) offers a standard HW floating point library, Verilog does not.
In order for *PyXHDL* to be able to handle the *Float* type, a
[Verilog FPU Library](https://github.com/davidel/v_fplib) is included within its
standard libraries.
Note that this is a very simple library which has been tested, but likely not as
fully as it would call for a full IEEE754 compliance.

Arrays are created using the *X.mkarray()* API.

```Python
# Creates a (4, 4) array of UINT8 initialized with 0.
ARR = XL.mkvwire(X.mkarray(X.UINT8, 4, 4), 0)
```

Arrays are indexed in the standard Python way.

```Python
RES = ARR[1, 2] + ARR[i, j]
```

When creating bits sequence types (Sint, Uint, Bits), the last dimension of the type
shape is the number of bits. The example above shape for *ARR* will be (4, 4, 8).

Slicing the last dimension of a bits sequence type, will result in selecting the bits.

```Python
# C will will Bits(4)
C = ARR[0, 1, 2: 6]
```

Sliced assign works in a similar fashion:

```Python
# XOUT is X.UINT8 and A is X.Uint(4, 4, 8).
# Assign the first 4 bits of XOUT with the last 4 bits of A[1, 0] and assigns the
# last 4 bits of XOUT with the first 4 bits of A[0, 1].
XOUT[: 4] = A[1, 0, 4: 8]
XOUT[4: 8] = B[0, 1, : 4]
```

Also works assigning whole sub-arrays, if the type matches (in shape and core type):

```Python
# XOUT is X.Uint(6, 4, 8) and A is X.Uint(4, 4, 8).
XOUT[1] = A[2]
```

Complex Python slice operations (e.g *A[0 : 8 : 2]*) are not supported (though in theory
they could be expanded in element-wise operations on the complex slice component).


## Creating Modules/Entities

Creating a module/entity with *PyHDL* is simply a matter of defining a new class inheriting
from the *X.Entity* base class.

The class variable *PORTS* must be defined, specifying the names of the ports and their
direction.

Note that the port data type is not defined statically, but instead during instantiation,
allowing to use the same entity code for different types. Clearly the Python code defining
the entity should take care of creating intermediate types using the real input types,
and use code that is compatible with the entity inputs.

Note that the entity *PORTS* declaration:

```Python
class MyEntity(X.Entity):

  PORTS = 'A, B, =XOUT'
  ...
```

is equivalent to the fully expanded form:

```Python
class MyEntity(X.Entity):

  PORTS = (
    X.Port('A', X.IN),
    X.Port('B', X.IN),
    X.Port('XOUT', X.OUT),
  )
  ...
```

If a port name is prefixed with the "=" character, the port is an output one. If instead
is prefixed with a "+" character is an input/output one, otherwise (with no prefix at all)
it is an input only port.

If necessary, it is possible to restrict the port input types to specific types, using
the following syntax:

```Python
class MyEntity(X.Entity):

  PORTS = 'A:u*, B:u*, =XOUT:s16'
  ...
```

Above, the *A* and *B* ports are restricted to _unsigned_ types of any size, and the
*XOUT* output port to _signed_ 16 bits type.

This is equivalent to the fully expanded form:

```Python
class MyEntity(X.Entity):

  PORTS = (
    X.Port('A', X.IN, type='u*'),
    X.Port('B', X.IN, type='u*'),
    X.Port('XOUT', X.OUT, type='s16'),
  )
  ...
```

If more complex type checking is required, it is of course possible to be implementing
the logic within the *MyEntity* _\_\_init\_\_()_ method.

The processes defining the entity behavior should also be declared, using the
*@X.hdl_process(...)* decorator.

The *sens=* parameter of the *@X.hdl_process(...)* specifies the sensitivity list of the
process, and can either be a comma separated string of port names, a dictionary whose
keys are the port names, and the values instances of the *X.Sens* class, or a tuple/list
with a combination of those:

```Python
@X.hdl_process(sens='+CLK, RESET, READY')
def run():
  if RESET != 0:
    XOUT = 0
```

The **+** sign in front of an HDL variable name means positive edge (0->1, *POSEDGE*),
while a **-** means negative edge (1->0, *NEGEDGE*). The default is *LEVEL* edge, which
triggers at every change of the variable value.

The above could have also been written using the fully expanded *X.Sens(...)* object.

```Python
@X.hdl_process(
  sens=(dict(CLK=X.Sens(X.POSEDGE)), 'RESET, READY'),
)
def run():
  if RESET != 0:
    XOUT = 0
```

The *kind=* parameter of the *@X.hdl_process(...)* specifies the process kind. If not
defined, the process is a normal process, with its code enclosed within a process block.

Declaring the process as **root** will lead to the code generated from the function, to
be emitted outside of any process block, within the entity root section.

```Python
@X.hdl_process(kind=X.ROOT_PROCESS)
def root():
  temp = X.mkwire(A.dtype)
  temp = A + B
  XOUT = temp * 3
```

Which produces the following Verilog code:

```Verilog
module Ex2(A, B, XOUT);
  input logic [7: 0] A;
  input logic [7: 0] B;
  output logic [7: 0] XOUT;
  wire logic [7: 0] temp;
  assign temp = A + B;
  assign XOUT = 8'(temp * 3);
endmodule
```

And VHDL code:

```VHDL
architecture behavior of Ex2 is
  signal temp : unsigned(7 downto 0);
begin
  temp <= A + B;
  XOUT <= resize(temp * 3, 8);
end architecture;
```

Note that there is no need to declare the ports variables as inputs of the process
functions, as those are implicitly defined by *PyXHDL* before interpreting the function
AST code. The same thing is true for any of the *kwargs* passed during an *Entity*
instantiation, which get the default values from the *Entity* *ARGS* class variable.

If a given *Entity* is instantiated with different input types (or even keyword arguments)
as many unique entities will be generated in the HDL emitted code.

The name of the functions within an entity (which will become the name of the processes
if the *@X.hdl_process(...)* decorator is used), as well as the names of the HDL entity
inputs and variables, must not conflict with VHDL/Verilog reserved keywords.

Example of simple gates composition in *PyXHDL*:

```Python
import pyxhdl as X
from pyxhdl import xlib as XL


class AndGate(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def run():
    XOUT = A & B


class NotGate(X.Entity):

  PORTS = 'A, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def run():
    XOUT = ~A


class NandGate(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def run():
    OOUT = X.mkwire(XOUT.dtype)
    AndGate(A=A,
            B=B,
            XOUT=OOUT)
    NotGate(A=OOUT,
            XOUT=XOUT)
```

It is also possible to have *Entity* other configuration as Python typical *kwargs*
during entity instantiation. This requires the inherited *Entity* to declare the
*ARGS* class variable defining the valid *kwargs* and their default values.

Example declaration:

```Python
class ArgsEntity(X.Entity):

  PORTS = 'CLK, XIN, =XOUT'

  ARGS = dict(mask=31)

  @X.hdl_process(sens='+CLK, XIN')
  def run():
    XOUT = XIN ^ mask
```

Example instantiation:

```Python
class UseArgsEntity(X.Entity):

  PORTS = 'CLK, A, B, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def use_proc():
    OOUT = X.mkwire(A.dtype)
    ArgsEntity(CLK=CLK,
               XIN=A,
	       XOUT=OOUT,
	       mask=63)
    ...
```


## Generating For AutoGenerated Code

It is possible to combine the flixibilty that Python offers as scripting language, with
the code generation capabilities of *PyXHDL* to generate the Python code to be parsed.

```Python
import py_misc_utils.template_replace as pytr

import pyxhdl as X
from pyxhdl import xlib as XL

class And(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def run():
    XOUT = A & B


_TEMPLATE = """
And(A=A[$i], B=B[$i], XOUT=XOUT[$i])
"""

class Ex3(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def run():
    for i in range(A.dtype.nbits):
      code = pytr.template_replace(_TEMPLATE, vals=dict(i=i))
      XL.xexec(code)
```

Which generates the following Verilog code.

```Verilog
// Entity "Ex3" is "Ex3" with:
// 	args={'A': 'bits(4)', 'B': 'bits(4)', 'XOUT': 'bits(4)'}
// 	kwargs={}
module Ex3(A, B, XOUT);
  input logic [3: 0] A;
  input logic [3: 0] B;
  output logic [3: 0] XOUT;
  And And_1(
    .A(A[0]),
    .B(B[0]),
    .XOUT(XOUT[0])
  );
  And And_2(
    .A(A[1]),
    .B(B[1]),
    .XOUT(XOUT[1])
  );
  And And_3(
    .A(A[2]),
    .B(B[2]),
    .XOUT(XOUT[2])
  );
  And And_4(
    .A(A[3]),
    .B(B[3]),
    .XOUT(XOUT[3])
  );
endmodule
// Entity "And" is "And" with:
// 	args={'A': 'bits(1)', 'B': 'bits(1)', 'XOUT': 'bits(1)'}
// 	kwargs={}
module And(A, B, XOUT);
  input logic A;
  input logic B;
  output logic XOUT;
  assign XOUT = A & B;
endmodule
```

The above is only an example of using the *XL.xexec()* API, as that could have been
simply done with a bare *And* entity instantiation loop (generating the exact same code).

```Python
import py_misc_utils.utils as pyu

import pyxhdl as X
from pyxhdl import xlib as XL

class And(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def run():
    XOUT = A & B


class Ex3(X.Entity):

  PORTS = 'A, B, =XOUT'

  @X.hdl_process(kind=X.ROOT_PROCESS)
  def run():
    for i in range(A.dtype.nbits):
      And(A=A[i], B=B[i], XOUT=XOUT[i])
```


## Loading External Libraries

*PyXHDL* loads its support libraries from the package *hdl_libs/{BACKEND}* folder,
according to the *LIBS* manifest file present within such folder.

On top of the required libraries, the user can also inject its owns, by the following
means:

  - Define the environment variable *PYXHDL_{BACKEND}_LIBS* to contain a semicolon
    separated list of source files to load.

  - List the library files within the configuration file, under the ```libs.{BACKEND}```
    key. Files listed there can be aither absolute paths, or paths relative to the
    configuration file path folder.
    ```
    libs:
      VHDL:
        - /PATH/TO/LIB
        - ...
    ```

It is also possible to register HDL specific modules at runtime using the *XL.register_module()*
API.

Furthermore, although the Python functions marked with *@X.hdl* and *@X.hdl_process(...)*
decorators lead to inlined HDL code, it is possible to define an inject HDL
functions from within *PyXHDL* and use them as normal Python functions.

See the example below that shows how to use *XL.register_module()* and *XL.create_function()*
to register HDL specific code to be used within *PyXHDL*.

```Python
MY_VHDL_MODULE = """
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package mypkg is
  function func(a : in unsigned; b : in unsigned) return unsigned;
  procedure proc(a : in unsigned; b : in unsigned);
end package;

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package body mypkg is
  function func(a : in unsigned; b : in unsigned) return unsigned is
  begin
    return a + b;
  end function;

  procedure proc(a : in unsigned; b : in unsigned) is
  begin
    assert a > b report "Compare failed!" severity error;
  end procedure;
end package body;
"""

def not_in_global_context(...):
  # If XL.register_module() is called from a global context (or more in general,
  # when no CodeGen context are active), it will register modules globally.
  # Register globally here means that running multiple generations from within the
  # same Python process will find the module regsitered.
  # Otherwise the module will be registered within the active CodeGen context.
  # For anyone using the `generator` module to emit HDL code (which will be the
  # majority), there will be no difference between global and context-local registrations.
  XL.register_module('mypkg', {X.VHDL: MY_VHDL_MODULE})

  # Note that the 'mypkg' argument to *XL.register_module()* is just a unique ID
  # (further registrations with such ID will override the previous ones) which does
  # not have to match the HDL package/module name (though it likely helps if it does
  # resemble it).

# Versus ...
# This will register globally. This and not_in_global_context() should not be used at
# the same time.
XL.register_module('mypkg', {X.VHDL: MY_VHDL_MODULE})

# Then it is possible to define Python functions using them, like describe below.
# Note that we we did not register the Verilog variant with the XL.register_module()
# above, so any attempt to use the APIs defined below while selecting a Verilog
# backend will fail.
my_func = XL.create_function('my_func',
                             {
                               X.VHDL: 'mypkg.func',
                               X.VERILOG: 'mypkg.func',
                             },
                             fnsig='u*, u*',
                             dtype=XL.argn_dtype(0))
my_proc = XL.create_function('my_proc',
                             {
                               X.VHDL: 'mypkg.proc',
                               X.VERILOG: 'mypkg.proc',
                             },
                             fnsig='u*, u*')

@X.hdl
def using_userdef(a, b):
  c = my_func(a + b, b - a)
  my_proc(a, c * 17)
```

Note that calls to *my_func()* and *my_proc()* will emit a function/procedure call
in the target HDL backend, and will not get inlined (though at the end they will, by
the backend HDL compiler in order to generate the matching HW).

The *dtype* argument to *XL.create_function()* can be a direct *X.Type* object, or
a lambda to which the arguments of a call are passed, and has to return the proper
type. In the above example, the utility *XL.argn_dtype()* is used, to return a lambda
which returns the type of the 0-th (first) argument.


## Placing External Modules/Entities

It is also possible to create entities class which are not defined within the *PyXHDL*
Python framework, but which instead refers to external entities (IP blocks). This is
accomplished by simply defining an *X.Entity* subclass with the *NAME* class property
specified (this is the full entity path, included the package scope, if any).

```Python
class ExternIP(X.Entity):

  PORTS = 'IN_A:u*, IN_B:u*, =OUT_DATA:u*'
  NAME = 'extern_pkg.Entity'

```

After that it can be instantiated like a normal *PyXHDL* entity.

```Python
# To be called from a root process.
ExternIP(IN_A=A,
         IN_B=B,
         OUT_DATA=XOUT,
         _P=dict(NBITS=A.dtype.nbits,
                 SIGNED=1))
```

The *extern_pkg.Entity* will have to be defined in backend specific library files to be
loaded within *PyXHDL* (see [Loading External Libraries](#loading-external-libraries)).

The *_P* argument allow to specify module/entity instantiation parameters/generics.

The *XL.ExternalEntity()* class should be used from the root process of a module or entity,
otherwise the generated code will not be valid.

Note that modules/entities defined with Python using *PyXHDL* can be instatiated by
simply constructing an object of that class from within a root process:

```Python
@X.hdl_process(kind=X.ROOT_PROCESS)
def root():
  OOUT = X.mkwire(XOUT.dtype)
  # AndGate defined within the PyXHDL Python framework.
  AndGate(A=A,
          B=B,
          XOUT=OOUT)
```


## Code Generation

In order to generate code for the target backend, the *generator* module is used,
like in the following example:

```Shell
$ python -m pyxhdl.generator \
    --input_file src/my_entity.py \
    --entity MyEntity \
    --backend VHDL \
    --inputs 'CLK,RESET,READY=mkwire(BIT)' \
    --inputs 'A,B,XOUT=mkwire(UINT8)' \
    --kwargs 'mode="simple"' \
    --kwargs 'steps=8' \
    --output_file my_entity.vhd
```

The *--input_file* argument specifies the path to the Python file defining the
root entity, while the *--entity* sets the name of the root entity itself.

The example above specifies the **CLK**, **RESET** and **READY** ports of the
root entity to be one bit, while the **A**, **B** and **XOUT** ones to be 8bit
unsigned integers.

It is also possible to pass keyword arguments to the entity, allowing runtime
configuration similar to what *VHDL* generics do (note that string inputs should
be quoted). This requires the user inherited *Entity* to specify the keyword
arguments within the *ARGS* class variable of the new entity.


## TestBench Code Generation

Using the same *generator* module, it is possible to generate a *testbench*
feeding the generator itself with the input data (*YAML* or *JSON*) to be used
for the test.

```Shell
$ python -m pyxhdl.generator \
    --input_file src/my_entity.py \
    --entity MyEntity \
    --backend VHDL \
    --inputs 'CLK,RESET,READY=mkwire(BIT)' \
    --inputs 'A,B,XOUT=mkwire(UINT8)' \
    --kwargs 'mode="simple"' \
    --kwargs 'steps=8' \
    --output_file my_entity_tb.vhd \
    --testbench \
    --tb_input_file test/my_entity_input_data.yaml \
    --tb_clock 'CLK,10'
```

The *--testbench* argument triggers the *testbench* module code generation.

The *--tb_input_file* points to the input data file for the test (both *YAML*
and *JSON* are supported), which has the following format:

```YAML
conf:
  loaders:
    - A:
        dtype: uint8
        kind: numpy
    - B:
        dtype: uint8
        kind: numpy
data:
  - RESET: 1
    _wait_expr: XL.wait_rising(CLK)
  - RESET: 0
    _wait_expr: XL.wait_rising(CLK)
  - A: 17
    B: 21
    XOUT: 134
    _wait_expr: XL.wait_rising(CLK)
  - A: 3
    B: 11
    XOUT: 77
    _wait_expr: XL.wait_rising(CLK)
  - ...
```

The *loaders* section of the input data is optional, and if missing the input
types will be the ones created by the *YAML* (or *JSON*) parser.

The *testbench* works by iterating the *data* section, setting the inputs to the
specified values, waiting according to the *_wait_expr* rule (see below for
more options), and comparing the outputs of the module/entity with the expected
values specified by the data.

The wait condition can also be specified in the command line, using the *--tb_wait*
argument. The *--tb_wait* specifies a wait time in nanoseconds. In case the
*--tb_wait* option is used in the command line, there is no need for *_wait_expr*
entries in the data.

Via the *--tb_clock_sync* argument it is also possible to configure a different
wait rule, specifying the clock port name and the sync mode. Example:

```
--tb_clock_sync 'CLK,rising'
```

In such cases, there is no need for the explicit *_wait_expr* in the input data
at all.

The *--tb_clock* enables the generation of a clock signal, on the specified port.
For example, to generate a 10ns period clock signal on the **CLK** port:

```
--tb_clock 'CLK,10'
```

A simpler version of the run above, using command line specified wait/sync
could be:

```Shell
$ python -m pyxhdl.generator \
    --input_file src/my_entity.py \
    --entity MyEntity \
    --backend VHDL \
    --inputs 'CLK,RESET,READY=mkwire(BIT)' \
    --inputs 'A,B,XOUT=mkwire(UINT8)' \
    --kwargs 'mode="simple"' \
    --kwargs 'steps=8' \
    --output_file my_entity_tb.vhd \
    --testbench \
    --tb_input_file test/my_entity_input_data.yaml \
    --tb_clock 'CLK,10' \
    --tb_clock_sync 'CLK,rising'
```

With data:

```YAML
data:
  - RESET: 1
  - RESET: 0
  - A: 17
    B: 21
    XOUT: 134
  - A: 3
    B: 11
    XOUT: 77
  - ...
```

Essentially the *testbench* iterates through each data entry, feed the tested
entity input ports with the data specified in the current entry (if an entry
does not contain data for an input, such input is not changed from the previous
one), wait according to the specified rules, and then compares the ouput ports
of the tested entity with the matching data in the current entry.
Same as the inputs, if the current entry does not contain data for a given output
port, nothing is compared for that port.

So, taking as example the above test data, the *testbench* will generate HDL
code to:

 - Set the **RESET** input to 1, and wait for the **CLK** rising edge (according
   to the *--tb_clock_sync* command line argument).

 - Set the **RESET** input to 0, and wait for the **CLK** rising edge.

 - Set the tested entity input ports **A** and **B** to 17 and 21 respectively,
   wait for the **CLK** rising edge, and then compare the **XOUT** ouput port
   with 134.

 - Set the tested entity input ports **A** and **B** to 3 and 11 respectively,
   wait for the **CLK** rising edge, and then compare the **XOUT** ouput port
   with 77.

 - ...

## Less Used Features

Below are briefly illustrated some less common features which are supported, with
the generated VHDL code letting explain their purpose:

```Python
# 1
XL.wait_until(A == 1)

# 2
with XL.context(delay=10):
  ctx = A * B
```

Generated VHDL code assuming *A* and *B* being an *X.UINT8* and *CLK* an *X.BIT*:

```VHDL
-- 1
wait until (A = to_unsigned(1, 8));

-- 2
ctx <= resize(A * B, 8) after 10 ns;
```

*PyXHDL* uses the new Python *MATCH*/*CASE* statement to map that to the appropriate
HDL case select construct. The *CASE* values need to be constants.

Example:

```Python
@X.hdl_process(sens='A, B')
def tester():
  match A:
    case 17:
      XOUT = A + 1
    case 21:
      XOUT = A + B
    case 34:
      XOUT = A - B
    case _:
      XOUT = A * B
```

Will map to VHDL:

```VHDL
architecture behavior of MatchEnt is
begin
  tester : process (A, B)
  begin
    case A is
      when to_unsigned(17, 8) =>
        XOUT <= A + 1;
      when to_unsigned(21, 8) =>
        XOUT <= A + B;
      when to_unsigned(34, 8) =>
        XOUT <= A - B;
      when others =>
        XOUT <= resize(A * B, 8);
    end case;
  end process;
end architecture;
```


## Verifying Generated HDL Output

A script is provided to verify the output generated by *PyXHDL*.

It can be used to verify both VHDL (with **GHDL** and **Vivado**) and Verilog (**Vivado**
and **Verilator**).

Example use to verify a generated VHDL file *generate_output.vhd* with a *RootEntity* top:

```Shell
$ python3 tools/verify.py --input generate_output.vhd --backend VHDL --entity RootEntity
```

