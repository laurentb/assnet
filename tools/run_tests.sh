#!/bin/bash

if [ "$1" != "" ]; then
    nosetests -sv $(dirname $0)/../tests/$1_test.py
else
    nosetests --all-modules -sv $(dirname $0)/../tests
fi
