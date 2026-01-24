
LOGLEV = INFO
SOURCES = axis_echo.py axis_tb.yaml
IFC_SOURCES = axis_echo_ifc.py axis_tb.yaml

TARGETS = axis_tb.vhd axis_tb.sv axis_tb_ifc.vhd axis_tb_ifc.sv


all: ${TARGETS}


axis_tb.vhd: ${SOURCES}
	python -m pyxhdl.generator \
		--input_file axis_echo.py \
		--entity AxisEcho \
		--backend vhdl \
		--inputs "CLK,RST_N,WREN,RDEN=mkvreg(BIT, 0)" \
		--inputs "WDATA,RDATA=mkvreg(Bits(32), 0)" \
		--testbench \
		--tb_clock "CLK,10" \
		--tb_input_file axis_tb.yaml \
		--log_level ${LOGLEV} \
		--output_file axis_tb.vhd

axis_tb.sv: ${SOURCES}
	python -m pyxhdl.generator \
		--input_file axis_echo.py \
		--entity AxisEcho \
		--backend verilog \
		--inputs "CLK,RST_N,WREN,RDEN=mkvreg(BIT, 0)" \
		--inputs "WDATA,RDATA=mkvreg(Bits(32), 0)" \
		--testbench \
		--tb_clock "CLK,10" \
		--tb_input_file axis_tb.yaml \
		--log_level ${LOGLEV} \
		--output_file axis_tb.sv

axis_tb_ifc.vhd: ${IFC_SOURCES}
	python -m pyxhdl.generator \
		--input_file axis_echo_ifc.py \
		--entity AxisEcho \
		--backend vhdl \
		--inputs "CLK,RST_N,WREN,RDEN=mkvreg(BIT, 0)" \
		--inputs "WDATA,RDATA=mkvreg(Bits(32), 0)" \
		--testbench \
		--tb_clock "CLK,10" \
		--tb_input_file axis_tb.yaml \
		--log_level ${LOGLEV} \
		--output_file axis_tb_ifc.vhd

axis_tb_ifc.sv: ${IFC_SOURCES}
	python -m pyxhdl.generator \
		--input_file axis_echo_ifc.py \
		--entity AxisEcho \
		--backend verilog \
		--inputs "CLK,RST_N,WREN,RDEN=mkvreg(BIT, 0)" \
		--inputs "WDATA,RDATA=mkvreg(Bits(32), 0)" \
		--testbench \
		--tb_clock "CLK,10" \
		--tb_input_file axis_tb.yaml \
		--log_level ${LOGLEV} \
		--output_file axis_tb_ifc.sv

clean:
	rm -f ${TARGETS}

.PHONY: clean
