#!/bin/sh -xe

if [ -z "${NOSE}" ]; then
    which nosetests >/dev/null 2>&1 && NOSE=$(which nosetests)
    which nosetests2 >/dev/null 2>&1 && NOSE=$(which nosetests2)
fi

if [ "$1" == '--slow' ]; then
    ASS2M_FAST_TEST=0
    shift
else
    ASS2M_FAST_TEST=1
fi
export ASS2M_FAST_TEST

if [ "$1" != "" ]; then
    ${NOSE} -sv $(dirname $0)/../tests/$1_test.py
else
    ${NOSE} --all-modules -sv $(dirname $0)/../tests
fi
