#!/usr/bin/env bash


SDIR=$(dirname "$0")
TDIR=$(dirname "$SDIR")
TESTDIR="${TESTDIR:-${TDIR}/data}"
WDIR=$(mktemp -d --suffix $(basename $0))

GHDL=$(which ghdl)
VERILATOR=$(which verilator)

# We need to handle slice-of-slice which Verilator agrees on, while slang do not.
# SLANG=$(which slang)


exit_cleanup() {
    test -d "$WDIR" && rm -fr "$WDIR"
}

trap exit_cleanup EXIT

set -e

for HDLF in $(ls -1 "$TESTDIR"/*.sv 2> /dev/null); do
    if [[ ! -z "$VERILATOR" ]]; then
        echo "[VERILATOR] Analyzing $HDLF ..."

        "$VERILATOR" --quiet -sv --lint-only --timing -Mdir "$WDIR" "$HDLF"
        rm -f "$WDIR"/work*.cf
    fi
    if [[ ! -z "$SLANG" ]]; then
        echo "[SLANG] Analyzing $HDLF ..."

        "$SLANG" -q --std latest --allow-hierarchical-const "$HDLF"
    fi
done

for HDLF in $(ls -1 "$TESTDIR"/*.vhd 2> /dev/null); do
    if [[ ! -z "$GHDL" ]]; then
        echo "[GHDL] Analyzing $HDLF ..."

        "$GHDL" -a --std=08 --workdir="$WDIR" "$HDLF"
        rm -f "$WDIR"/work*.cf
    fi
done

