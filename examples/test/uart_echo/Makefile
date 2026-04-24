
WORKDIR ?= /tmp
SRCDIR ?= $(dir $(realpath $(lastword ${MAKEFILE_LIST})))
LOG_LEVEL ?= INFO
CLK_FREQ ?= 100000000
BAUD_RATE ?= 115200
NUM_TESTS ?= 25

CLK = $(shell expr 1000000000 / ${CLK_FREQ})ns


all: uart_echo

uart_echo:
	python -m pyxhdl.tools.unit_test \
		--log_level ${LOG_LEVEL} \
		--inputs ${SRCDIR}/uart_echo.py \
		--entity UartEcho \
		--tb_input_file ${SRCDIR}/tb_generator.py \
		--tb_inputs "CLK,RST_N,UIN,UOUT,CTS,RTS=mkvreg(BIT, 0)" \
			"clk_freq=${CLK_FREQ}" \
			"baud_rate=${BAUD_RATE}" \
			"num_tests=${NUM_TESTS}" \
		--gargs="--tb_clock;CLK,${CLK}"

