#!/bin/sh -xe

if [ "$1" == '--slow' ]; then
    ASS2M_FAST_TEST=0
    shift
else
    ASS2M_FAST_TEST=1
fi
export ASS2M_FAST_TEST

if [ "$1" != "" ]; then
    nosetests -sv $(dirname $0)/../tests/$1_test.py
else
    nosetests --all-modules -sv $(dirname $0)/../tests
fi
