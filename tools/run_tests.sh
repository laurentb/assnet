#!/bin/bash -e

if [ -z "${NOSE}" ]; then
    which nosetests >/dev/null 2>&1 && NOSE=$(which nosetests)
    which nosetests2 >/dev/null 2>&1 && NOSE=$(which nosetests2)
fi

if [ "$1" == '--slow' ]; then
    export ASS2M_FAST_TEST=0
    shift
else
    export ASS2M_FAST_TES=1
fi

if [ "$1" != "" ]; then
    ${NOSE} -sv $(dirname $0)/../tests/${1}_test.py
else
    ${NOSE} --all-modules -sv $(dirname $0)/../tests
fi
