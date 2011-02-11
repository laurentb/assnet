# -*- coding: utf-8 -*-

# Copyright(C) 2011  Romain Bignon, Laurent Bachelier
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import sys
import os

from ass2m import Ass2m
from ass2m.plugin import Plugin
from ass2m.cmd import Command

class TreeCmd(Command):
    DESCRIPTION = 'Display the working tree'
    WORKDIR = True

    def cmd(self, args):
        for root, directories, files in os.walk(os.getcwd()):
            path = root[len(os.getcwd()):]
            depth = path.count('/')
            f = self.ass2m.storage.get_file(path)
            parent = f.parent()

            perms_s = ''
            for key, perm in f.perms.iteritems():
                if not parent or not key in parent.perms or parent.perms[key] != perm:
                    perms_s += '%s(%s) ' % (key, f.perm_str(perm))

            if len(perms_s) == 0:
                continue

            print '%-40s %s' % ('  ' * depth + path + '/', perms_s)

class InitCmd(Command):
    DESCRIPTION = 'Initialize the current directory as working tree'
    WORKDIR = False

    def cmd(self, args):
        if self.ass2m.storage:
            print >>sys.stderr, 'Error: %s is already a working directory' % os.getcwd()
            return 1

        self.ass2m.create(os.getcwd())
        print 'Ass2m working directory created.'

class CorePlugin(Plugin):
    def __init__(self, ass2m):
        self.ass2m = ass2m
        self.register_cli_command('tree', TreeCmd)
        self.register_cli_command('init', InitCmd)
