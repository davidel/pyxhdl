#!/usr/bin/env bash

set -ex

SDIR=$(dirname "$0")
TDIR=$(dirname "$SDIR")
TESTDIR="${TESTDIR:-${TDIR}/data}"
WDIR=$(mktemp -d --suffix $(basename $0))
GHDL="ghdl"

exit_cleanup() {
    test -d "$WDIR" && rm -fr "$WDIR"
}

trap exit_cleanup EXIT

for VHF in "$TESTDIR"/*.vhd; do
    echo "Analyzing $VHF ..."
    "$GHDL" -a --std=08 --workdir=$WDIR $VHF
    rm -f "$WDIR"/work*.cf
done

