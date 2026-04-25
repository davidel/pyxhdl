#!/usr/bin/env bash

set -e

SDIR=$(dirname "$0")
TDIR=$(dirname "$SDIR")
TESTDIR="${TESTDIR:-${TDIR}/data}"
WDIR=$(mktemp -d --suffix $(basename $0))

GHDL=$(which ghdl)
VERILATOR=$(which verilator)

exit_cleanup() {
    test -d "$WDIR" && rm -fr "$WDIR"
}

trap exit_cleanup EXIT

VERILATOR_CMDLN=()
if [[ ! -z "$VERILATOR" ]]; then
    if [[ ! -z $("$VERILATOR" --help | egrep -o -- '--quiet ') ]]; then
        VERILATOR_CMDLN+=(--quiet)
    fi
fi

for HDLF in $(ls -1 "$TESTDIR"/*.sv 2> /dev/null); do
    if [[ ! -z "$VERILATOR" ]]; then
        echo "[VERILATOR] Analyzing $HDLF ..."

        "$VERILATOR" "${VERILATOR_CMDLN[@]}" -sv --lint-only --timing -Mdir "$WDIR" "$HDLF"
        rm -f "$WDIR"/work*.cf
    fi
done

for HDLF in $(ls -1 "$TESTDIR"/*.vhd 2> /dev/null); do
    if [[ ! -z "$GHDL" ]]; then
        echo "[GHDL] Analyzing $HDLF ..."

        "$GHDL" -a --std=08 --workdir="$WDIR" "$HDLF"
        rm -f "$WDIR"/work*.cf
    fi
done

