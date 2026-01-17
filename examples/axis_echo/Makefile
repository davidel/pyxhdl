
LOGLEV = INFO
SOURCES = axis_echo.py axis_tb.yaml


all: axis_tb.vhd axis_tb.sv


axis_tb.vhd: ${SOURCES}
	python -m pyxhdl.generator \
		--input_file axis_echo.py \
		--entity AxisEcho \
		--backend VHDL \
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
		--backend Verilog \
		--inputs "CLK,RST_N,WREN,RDEN=mkvreg(BIT, 0)" \
		--inputs "WDATA,RDATA=mkvreg(Bits(32), 0)" \
		--testbench \
		--tb_clock "CLK,10" \
		--tb_input_file axis_tb.yaml \
		--log_level ${LOGLEV} \
		--output_file axis_tb.sv


clean:
	rm -f axis_tb.vhd axis_tb.sv

.PHONY: clean
