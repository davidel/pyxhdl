
WORKDIR ?= /tmp
SRCDIR ?= $(dir $(realpath $(lastword ${MAKEFILE_LIST})))
LOG_LEVEL ?= INFO
DATA_SOURCE ?= ${SRCDIR}/tb_generator.py
CLK_FREQ ?= 100000000
BAUD_RATE ?= 115200
NUM_TESTS ?= 100
SOURCES = ${SRCDIR}/uart_echo.py ${DATA_SOURCE}

CLK = $(shell expr 1000000000 / ${CLK_FREQ})ns

VHDL_TARGET = ${WORKDIR}/uart_tb.vhd
SV_TARGET = ${WORKDIR}/uart_tb.sv

TARGETS = ${VHDL_TARGET} ${SV_TARGET}


all: ${TARGETS}


${VHDL_TARGET}: ${SOURCES}
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
		--output_file ${VHDL_TARGET}

${SV_TARGET}: ${SOURCES}
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
		--output_file ${SV_TARGET}

clean:
	rm -f ${TARGETS}

.PHONY: clean
