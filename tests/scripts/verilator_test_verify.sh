#!/usr/bin/env bash

set -ex

SDIR=$(dirname "$0")
TDIR=$(dirname "$SDIR")
TESTDIR="${TESTDIR:-${TDIR}/data}"
WDIR=$(mktemp -d --suffix $(basename $0))
VERILATOR="verilator"

exit_cleanup() {
    test -d "$WDIR" && rm -fr "$WDIR"
}

trap exit_cleanup EXIT

for SVF in "$TESTDIR"/*.sv; do
    echo "Analyzing $SVF ..."
    "$VERILATOR" --quiet -sv --lint-only --timing -Mdir "$WDIR" "$SVF"
    rm -f "$WDIR"/work*.cf
done

