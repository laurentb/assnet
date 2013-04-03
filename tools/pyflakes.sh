#!/bin/bash -u
cd $(dirname $0)
cd ..
grep -r --include '*.py' 'class [^( ]\+:$' . && exit 3
grep -r --include '*.py' $'\t\|\s$' . && exit 4

FLAKE8=""
if which flake8 >/dev/null 2>&1; then
    FLAKE8=flake8
fi
if which flake8-python2 >/dev/null 2>&1; then
    FLAKE8=flake8-python2
fi

if [ -n "${FLAKE8}" ]; then
    set -e
    ${FLAKE8} --ignore=E,W *.py assnet tests bin/*
else
    # grep will return 0 only if it founds something, but our script
    # wants to return 0 when it founds nothing!
    pyflakes *.py assnet tests bin/* | grep -v redefinition && exit 1 || exit 0
fi
