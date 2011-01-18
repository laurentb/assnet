# -*- coding: utf-8 -*-

import sys
import os

from ass2m import Ass2m, NotWorkingDir

class Ass2mCLI(object):
    def __init__(self):
        try:
            self.ass2m = Ass2m(os.getcwd())
        except NotWorkingDir:
            self.ass2m = None

    def process_command(self, argv):
        if len(argv) < 2 or not hasattr(self, 'cmd_%s' % argv[1]):
            return self.cmd_help([])

        func = getattr(self, 'cmd_%s' % argv[1])

        return func(argv[2:])

    def workdir(func):
        def inner(self, *args, **kwargs):
            if not self.ass2m:
                print >>sys.stderr, 'Error: Not a ass2m working directory.'
                print >>sys.stderr, 'Please use "%s init"' % sys.argv[0]
                return 1
            return func(self, *args, **kwargs)
        return inner

    def cmd_help(self, args):
        print 'Usage: %s cmd [args..]' % sys.argv[0]
        print ''
        print 'Commands:'
        print '    init'
        print '    share PATH [CONTACTS..]'

    @workdir
    def cmd_share(self, args):
        return

    def cmd_init(self, args):
        if self.ass2m:
            print >>sys.stderr, 'Error: %s is already a working directory' % os.getcwd()
            return 1

        self.ass2m = Ass2m.create(os.getcwd())
        print 'Ass2m working directory created.'
