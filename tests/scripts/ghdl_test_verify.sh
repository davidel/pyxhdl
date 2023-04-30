#!/usr/bin/env bash

set -ex

SDIR=$(dirname "$0")
TDIR=$(dirname "$SDIR")
WDIR=$(mktemp -d -t $(basename $0))

exit_cleanup() {
    test -d "$WDIR" && rm -fr "$WDIR"
}

trap exit_cleanup EXIT

for VHF in $TDIR/data/*.vhd; do
    echo "Analyzing $VHF ..."
    ghdl -a --std=08 --workdir=$WDIR $VHF
    rm -f $WDIR/work*.cf
done

