
WORKDIR ?= /tmp
SRCDIR ?= $(dir $(realpath $(lastword ${MAKEFILE_LIST})))
LOG_LEVEL ?= INFO


all: axis_echo axis_echo_ifc


axis_echo:
	python -m pyxhdl.tools.unit_test \
		--log_level ${LOG_LEVEL} \
		--inputs ${SRCDIR}/axis_echo.py \
		--entity AxisEcho \
		--tb_input_file ${SRCDIR}/axis_tb.yaml \
		--tb_inputs "CLK,RST_N,WREN,RDEN=mkvreg(BIT, 0)" "WDATA,RDATA=mkvreg(Bits(32), 0)" \
		--gargs=--tb_clock \
		--gargs="CLK,10ns"

axis_echo_ifc:
	python -m pyxhdl.tools.unit_test \
		--log_level ${LOG_LEVEL} \
		--inputs ${SRCDIR}/axis_echo_ifc.py \
		--entity AxisEcho \
		--tb_input_file ${SRCDIR}/axis_tb.yaml \
		--tb_inputs "CLK,RST_N,WREN,RDEN=mkvreg(BIT, 0)" "WDATA,RDATA=mkvreg(Bits(32), 0)" \
		--gargs=--tb_clock \
		--gargs="CLK,10ns"

