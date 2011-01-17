#!/usr/bin/env python
from os import path
print 'var.basedir = "%s"' % path.realpath(path.join(path.dirname(__file__), '..', '..'))
