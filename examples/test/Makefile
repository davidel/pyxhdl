
SRCDIR ?= $(dir $(realpath $(lastword ${MAKEFILE_LIST})))


all: axis_echo uart_echo

axis_echo:
	make -C ${SRCDIR}/axis_echo

uart_echo:
	make -C ${SRCDIR}/uart_echo

.PHONY: axis_echo uart_echo
