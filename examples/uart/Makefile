
LOGLEV = INFO
SOURCES = uart_echo.py uart_tb.yaml

TARGETS = uart_tb.vhd uart_tb.sv


all: ${TARGETS}


uart_tb.vhd: ${SOURCES}
	python -m pyxhdl.generator \
		--input_file uart_echo.py \
		--entity UartEcho \
		--backend vhdl \
		--inputs "CLK,RST_N,UIN,UOUT,CTS,RTS=mkvreg(BIT, 0)" \
		--testbench \
		--tb_clock "CLK,10" \
		--tb_input_file uart_tb.yaml \
		--log_level ${LOGLEV} \
		--output_file uart_tb.vhd

uart_tb.sv: ${SOURCES}
	python -m pyxhdl.generator \
		--input_file uart_echo.py \
		--entity UartEcho \
		--backend verilog \
		--inputs "CLK,RST_N,UIN,UOUT,CTS,RTS=mkvreg(BIT, 0)" \
		--testbench \
		--tb_clock "CLK,10" \
		--tb_input_file uart_tb.yaml \
		--log_level ${LOGLEV} \
		--output_file uart_tb.sv

clean:
	rm -f ${TARGETS}

.PHONY: clean
