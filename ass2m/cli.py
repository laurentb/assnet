# -*- coding: utf-8 -*-

import sys
import os

from ass2m import Ass2m, WorkdirNotFound

class Ass2mCLI(object):
    def __init__(self):
        try:
            self.ass2m = Ass2m(os.getcwd())
        except WorkdirNotFound:
            self.ass2m = None

    def parse_args(self, argv):
        if len(argv) < 2 or not hasattr(self, 'cmd_%s' % argv[1]):
            return self.cmd_help([])

        func = getattr(self, 'cmd_%s' % argv[1])

        return func(argv[2:])

    def cmd_help(self, args):
        print 'Usage: %s cmd [args..]' % sys.argv[0]
        print ''
        print 'Commands:'
        print '    init'
        print '    share PATH [CONTACTS..]'

    def cmd_share(self, args):
        return

    def cmd_init(self, args):
        self.ass2m = Ass2m.create(os.getcwd())
        print 'Ass2m working directory created.'
