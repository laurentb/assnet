# -*- coding: utf-8 -*-

# Copyright (C) 2011 Romain Bignon, Laurent Bachelier
#
# This file is part of ass2m.
#
# ass2m is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ass2m is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with ass2m. If not, see <http://www.gnu.org/licenses/>.


import sys
import os

from ass2m.plugin import Plugin
from ass2m.cmd import Command
from ass2m.storage import Storage
from ass2m.files import File

from ass2m.routes import View
from ass2m.server import ViewAction, FileApp


__all__ = ['CorePlugin']


class InitCmd(Command):
    DESCRIPTION = 'Initialize the current directory as working tree'
    WORKDIR = False

    def cmd(self, args):
        if self.storage:
            print >>sys.stderr, 'Error: %s is already a working directory' % self.working_dir
            return 1

        self.storage = Storage.create(self.working_dir)
        print 'Ass2m working directory created.'

class TreeCmd(Command):
    DESCRIPTION = 'Display the working tree'
    WORKDIR = True

    def print_perms(self, path, depth):
        f = self.storage.get_file(path)
        parent = f.parent()

        perms_s = ''
        for key, perms in f.perms.iteritems():
            if not parent or not key in parent.perms or parent.perms[key] != perms:
                perms_s += '%s(%s) ' % (key, f.p2str(perms))

        if len(perms_s) == 0:
            return

        print '%-40s %s' % ('  ' * depth + path, perms_s)

    def cmd(self, args):
        for root, directories, files in os.walk(self.working_dir):
            path = root[len(self.storage.root):]
            depth = path.count('/')

            self.print_perms(path + '/', depth)
            for filename in files:
                self.print_perms(os.path.join(path, filename), depth+1)

class ChViewCmd(Command):
    DESCRIPTION = 'Change default view of a path'

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('view')
        parser.add_argument('path', nargs='+')

    def cmd(self, args):
        for path in args.path:
            if not os.path.exists(path):
                print >>sys.stderr, 'Error: Path "%s" does not exist.' % path
                continue

            f = self.storage.get_file_from_realpath(os.path.realpath(path))
            if not f:
                print >>sys.stderr, 'Error: Path "%s" is not in working directory.' % path
                continue

            f.view = args.view
            f.save()

class ChModCmd(Command):
    DESCRIPTION = 'Change permissions of a path'

    @staticmethod
    def configure_parser(parser):
        parser.prefix_chars = ''
        parser.add_argument('who')
        parser.add_argument('perms')
        parser.add_argument('path', nargs='+')

    def cmd(self, args):
        if '.' in args.who:
            t, who = args.who.split('.', 1)
            if t == 'u':
                if not self.storage.user_exists(who):
                    print >>sys.stderr, 'Error: User "%s" does not exist.' % who
                    return 1
            elif t == 'g':
                if not who in self.storage.get_groupscfg():
                    print >>sys.stderr, 'Error: Group "%s" does not exist.' % who
                    return 1
            else:
                print >>sys.stderr, 'Error: "%s" is not a right kind of target.' % t
                return 1
        elif args.who not in ('all', 'auth'):
            print >>sys.stderr, 'Error: "%s" is not a right target.' % args.who
            print >>sys.stderr, 'Only available ones: "u.<username>", "g.<group>", "auth", "all"'
            return 1

        if args.perms != '-':
            state = -1
            to_add = 0
            to_remove = 0
            for l in args.perms:
                if l == '+': state = 1
                elif l == '-': state = 0
                else:
                    try:
                        perm = File.str2p(l)
                    except KeyError:
                        print >>sys.stderr, 'Error: Perm "%s" does not exist.' % l
                        return 1
                    if state == 1:   to_add |= perm
                    elif state == 0: to_remove |= perm
                    else:
                        to_remove = File.PERM_ALL
                        to_add = perm
                        state = 1

        for path in args.path:
            if not os.path.exists(path):
                print >>sys.stderr, 'Error: Path "%s" does not exist.' % path
                continue

            f = self.storage.get_file_from_realpath(os.path.realpath(path))
            if not f:
                print >>sys.stderr, 'Error: Path "%s" is not in working directory.' % path
                continue

            if args.perms == '-':
                if args.who in f.perms:
                    f.perms.pop(args.who)
                    f.save()
            else:
                perms = f.perms.get(args.who, 0)
                f.perms[args.who] = (perms & ~to_remove) | to_add
                f.save()

class ResolveCmd(Command):
    DESCRIPTION = 'Get the storage name of a path'

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('path', nargs='+')

    def cmd(self, args):
        for path in args.path:
            if not os.path.exists(path):
                print >>sys.stderr, 'Error: Path "%s" does not exist.' % path
                continue

            f = self.storage.get_file_from_realpath(os.path.realpath(path))
            if not f:
                print >>sys.stderr, 'Error: Path "%s" is not in working directory.' % path
                continue
            print '%s => %s' % (f.path, os.path.join(self.storage.path, f._get_confname()))


class DownloadAction(ViewAction):
    def get(self):
        # serve the file, delegate everything to to FileApp
        self.ctx.res = FileApp(self.ctx.file.get_realpath())


class ListAction(ViewAction):
    def get(self):
        dirs = []
        files = []
        for f in self.ctx.iter_files():
            if f.isdir():
                dirs.append(f)
            else:
                files.append(f)

        self.ctx.template_vars['dirs'] = dirs
        self.ctx.template_vars['files'] = files
        self.ctx.res.body = self.ctx.render('list.html')


class CorePlugin(Plugin):
    def init(self):
        self.register_cli_command('init', InitCmd)
        self.register_cli_command('tree', TreeCmd)
        self.register_cli_command('chmod', ChModCmd)
        self.register_cli_command('chview', ChViewCmd)
        self.register_cli_command('resolve', ResolveCmd)

        self.register_web_view(
                View(object_type='file', name='raw'),
                DownloadAction, 10)
        self.register_web_view(
                View(object_type='directory', name='list', verbose_name='Detailed list'),
                ListAction, 10)
