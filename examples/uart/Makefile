
SRCDIR ?= .
LOG_LEVEL ?= INFO
DATA_SOURCE ?= tb_generator.py
CLK_FREQ ?= 100000000
BAUD_RATE ?= 115200
NUM_TESTS ?= 100
SOURCES = ${SRCDIR}/uart_echo.py ${DATA_SOURCE}

CLK = "$(shell expr 1000000000 / ${CLK_FREQ})ns"

TARGETS = uart_tb.vhd uart_tb.sv


all: ${TARGETS}


uart_tb.vhd: ${SOURCES}
	python -m pyxhdl.generator \
		--input_file ${SRCDIR}/uart_echo.py \
		--entity UartEcho \
		--backend vhdl \
		--inputs "CLK,RST_N,UIN,UOUT,CTS,RTS=mkvreg(BIT, 0)" \
		--inputs clk_freq=${CLK_FREQ} \
		--inputs baud_rate=${BAUD_RATE} \
		--inputs num_tests=${NUM_TESTS} \
		--testbench \
		--tb_clock CLK,${CLK} \
		--tb_input_file ${DATA_SOURCE} \
		--log_level ${LOG_LEVEL} \
		--output_file uart_tb.vhd

uart_tb.sv: ${SOURCES}
	python -m pyxhdl.generator \
		--input_file ${SRCDIR}/uart_echo.py \
		--entity UartEcho \
		--backend verilog \
		--inputs "CLK,RST_N,UIN,UOUT,CTS,RTS=mkvreg(BIT, 0)" \
		--inputs clk_freq=${CLK_FREQ} \
		--inputs baud_rate=${BAUD_RATE} \
		--inputs num_tests=${NUM_TESTS} \
		--testbench \
		--tb_clock CLK,${CLK} \
		--tb_input_file ${DATA_SOURCE} \
		--log_level ${LOG_LEVEL} \
		--output_file uart_tb.sv

clean:
	rm -f ${TARGETS}

.PHONY: clean
