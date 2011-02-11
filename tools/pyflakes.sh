#!/bin/bash
if [ `basename $PWD` == 'tools' ]; then
        cd ..
fi

# grep will return 0 only if it founds something, but our script
# wants to return 0 when it founds nothing!
pyflakes ass2m | grep -v redefinition && exit 1 || exit 0
