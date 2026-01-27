
LOG_LEVEL ?= INFO
DATA_SOURCE ?= uart_tb.yaml
CLK_FREQ ?= 50000000
BAUD_RATE ?= 115200
SOURCES = uart_echo.py ${DATA_SOURCE}

TARGETS = uart_tb.vhd uart_tb.sv


all: ${TARGETS}


uart_tb.vhd: ${SOURCES}
	python -m pyxhdl.generator \
		--input_file uart_echo.py \
		--entity UartEcho \
		--backend vhdl \
		--inputs "CLK,RST_N,UIN,UOUT,CTS,RTS=mkvreg(BIT, 0)" \
		--inputs clk_freq=${CLK_FREQ} \
		--inputs baud_rate=${BAUD_RATE} \
		--testbench \
		--tb_clock "CLK,10" \
		--tb_input_file ${DATA_SOURCE} \
		--log_level ${LOG_LEVEL} \
		--output_file uart_tb.vhd

uart_tb.sv: ${SOURCES}
	python -m pyxhdl.generator \
		--input_file uart_echo.py \
		--entity UartEcho \
		--backend verilog \
		--inputs "CLK,RST_N,UIN,UOUT,CTS,RTS=mkvreg(BIT, 0)" \
		--inputs clk_freq=${CLK_FREQ} \
		--inputs baud_rate=${BAUD_RATE} \
		--testbench \
		--tb_clock "CLK,10" \
		--tb_input_file ${DATA_SOURCE} \
		--log_level ${LOG_LEVEL} \
		--output_file uart_tb.sv

clean:
	rm -f ${TARGETS}

.PHONY: clean
