
SRCDIR ?= .
LOG_LEVEL ?= INFO
SOURCES = ${SRCDIR}/axis_echo.py ${SRCDIR}/axis_tb.yaml
IFC_SOURCES = ${SRCDIR}/axis_echo_ifc.py ${SRCDIR}/axis_tb.yaml

TARGETS = axis_tb.vhd axis_tb.sv axis_tb_ifc.vhd axis_tb_ifc.sv


all: ${TARGETS}


axis_tb.vhd: ${SOURCES}
	python -m pyxhdl.generator \
		--input_file ${SRCDIR}/axis_echo.py \
		--entity AxisEcho \
		--backend vhdl \
		--inputs "CLK,RST_N,WREN,RDEN=mkvreg(BIT, 0)" \
		--inputs "WDATA,RDATA=mkvreg(Bits(32), 0)" \
		--testbench \
		--tb_clock "CLK,10ns" \
		--tb_input_file ${SRCDIR}/axis_tb.yaml \
		--log_level ${LOG_LEVEL} \
		--output_file axis_tb.vhd

axis_tb.sv: ${SOURCES}
	python -m pyxhdl.generator \
		--input_file ${SRCDIR}/axis_echo.py \
		--entity AxisEcho \
		--backend verilog \
		--inputs "CLK,RST_N,WREN,RDEN=mkvreg(BIT, 0)" \
		--inputs "WDATA,RDATA=mkvreg(Bits(32), 0)" \
		--testbench \
		--tb_clock "CLK,10ns" \
		--tb_input_file ${SRCDIR}/axis_tb.yaml \
		--log_level ${LOG_LEVEL} \
		--output_file axis_tb.sv

axis_tb_ifc.vhd: ${IFC_SOURCES}
	python -m pyxhdl.generator \
		--input_file ${SRCDIR}/axis_echo_ifc.py \
		--entity AxisEcho \
		--backend vhdl \
		--inputs "CLK,RST_N,WREN,RDEN=mkvreg(BIT, 0)" \
		--inputs "WDATA,RDATA=mkvreg(Bits(32), 0)" \
		--testbench \
		--tb_clock "CLK,10ns" \
		--tb_input_file ${SRCDIR}/axis_tb.yaml \
		--log_level ${LOG_LEVEL} \
		--output_file axis_tb_ifc.vhd

axis_tb_ifc.sv: ${IFC_SOURCES}
	python -m pyxhdl.generator \
		--input_file ${SRCDIR}/axis_echo_ifc.py \
		--entity AxisEcho \
		--backend verilog \
		--inputs "CLK,RST_N,WREN,RDEN=mkvreg(BIT, 0)" \
		--inputs "WDATA,RDATA=mkvreg(Bits(32), 0)" \
		--testbench \
		--tb_clock "CLK,10ns" \
		--tb_input_file ${SRCDIR}/axis_tb.yaml \
		--log_level ${LOG_LEVEL} \
		--output_file axis_tb_ifc.sv

clean:
	rm -f ${TARGETS}

.PHONY: clean
