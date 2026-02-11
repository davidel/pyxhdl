
WORKDIR ?= /tmp
SRCDIR ?= $(dir $(realpath $(lastword ${MAKEFILE_LIST})))
LOG_LEVEL ?= INFO
MM_DIM_SIZE ?= 32
MM_TILE_SIZE ?= 8
MM_NSAMPLES ?= 4
MM_CLK ?= 10ns
MM_TOLL ?= 0.01
MM_DTYPE ?= FLOAT16
MM_DATA_FILE = ${WORKDIR}/matmul_data.yaml
MM_VHDL_FILE = ${WORKDIR}/matmul.vhd
MM_SVL_FILE = ${WORKDIR}/matmul.sv
VERILATOR_BINDIR ?= ${WORKDIR}/vobj
VERILATOR_OUTSPLIT ?= 1000
VERILATOR_OPT ?= -O0
VERILATOR_TRACE ?= --trace
VERILATOR_ASSERT ?= --assert
TARGETS = ${MM_DATA_FILE} ${MM_VHDL_FILE} ${MM_SVL_FILE}

all: ${TARGETS} hdl_generate

hdl_generate: ${MM_VHDL_FILE} ${MM_SVL_FILE}

${MM_DATA_FILE}:
	python ${SRCDIR}/matmul_gen_tbdata.py \
		--nsamples ${MM_NSAMPLES} \
		--dimsize ${MM_DIM_SIZE} \
		--output_file ${MM_DATA_FILE}

${MM_VHDL_FILE}: ${MM_DATA_FILE}
	python -m pyxhdl.generator \
		--backend vhdl \
		--input_file ${SRCDIR}/matmul.py \
		--entity MMUnit \
		--inputs "AROW,BROW,CROW=mkreg(mkarray(${MM_DTYPE}, ${MM_DIM_SIZE}))" \
		--inputs "CLK,RESET,COMPUTE,INFEED,OUTFEED,READY=mkvreg(BIT, 0)" \
		--kwargs tilesize=${MM_TILE_SIZE} \
		--testbench \
		--tb_input_file ${MM_DATA_FILE} \
		--tb_clock CLK,${MM_CLK} \
		--tb_toll ${MM_TOLL} \
		--log_level ${LOG_LEVEL} \
		--output_file ${MM_VHDL_FILE} \

${MM_SVL_FILE}: ${MM_DATA_FILE}
	python -m pyxhdl.generator \
		--backend verilog \
		--input_file ${SRCDIR}/matmul.py \
		--entity MMUnit \
		--inputs "AROW,BROW,CROW=mkreg(mkarray(${MM_DTYPE}, ${MM_DIM_SIZE}))" \
		--inputs "CLK,RESET,COMPUTE,INFEED,OUTFEED,READY=mkvreg(BIT, 0)" \
		--kwargs tilesize=${MM_TILE_SIZE} \
		--testbench \
		--tb_input_file ${MM_DATA_FILE} \
		--tb_clock CLK,${MM_CLK} \
		--tb_toll ${MM_TOLL} \
		--log_level ${LOG_LEVEL} \
		--output_file ${MM_SVL_FILE} \

mm_vhdl_test: ${MM_VHDL_FILE}
	ghdl \
		-c \
		--std=08 \
		${MM_VHDL_FILE} \
		-r Testbench

mm_svl_test: ${MM_SVL_FILE}
	verilator \
		${VERILATOR_TRACE} \
		${VERILATOR_ASSERT} \
		--binary \
		${VERILATOR_OPT} \
		-j 8 \
		--output-split ${VERILATOR_OUTSPLIT} \
		--Mdir ${VERILATOR_BINDIR} \
		-sv \
		--top-module TestBench \
		${MM_SVL_FILE}
	${VERILATOR_BINDIR}/VTestBench

clean:
	rm -rf ${TARGETS} ${VERILATOR_BINDIR}

.PHONY: clean
