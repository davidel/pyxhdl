#!/bin/sh

if [ -f Makefile ]; then
    make clean
fi

rm -rf \
   build/ \
   _deps/ \
   CMakeFiles/ \
   CMakeCache.txt \
   *.egg-info \
   *.cmake \
   test/CMakeFiles/ \
   test/*.cmake \
   test/Makefile

find . -name __pycache__ | xargs rm -rf

if [ -f CMakeList.txt ]; then
    rm -rf Makefile
fi

