#!/bin/bash
cd $(dirname $0)
cd ..

# grep will return 0 only if it finds something, but our script
# wants to return 0 when it finds nothing!
pyflakes ass2m | grep -v redefinition && exit 1 || exit 0
