# -*- coding: utf-8 -*-

# Copyright (C) 2011 Romain Bignon, Laurent Bachelier
#
# This file is part of assnet.
#
# assnet is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# assnet is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with assnet. If not, see <http://www.gnu.org/licenses/>.


import sys
import os

from paste.httpheaders import CONTENT_DISPOSITION

from assnet.plugin import Plugin
from assnet.cmd import Command
from assnet.storage import Storage
from assnet.files import File
from assnet.routes import View
from assnet.server import ViewAction, FileApp
from .cleanup import ICleaner
from .gallery import MediaListAction


__all__ = ['CorePlugin']


class InitCmd(Command):
    DESCRIPTION = 'Initialize the current directory as working tree'
    WORKDIR = False

    def cmd(self, args):
        if self.storage:
            print >>sys.stderr, 'Error: %s is already a working directory' % self.working_dir
            return 1

        self.storage = Storage.create(self.working_dir)
        print 'assnet working directory created.'


class TreeCmd(Command):
    DESCRIPTION = 'Display the working tree'
    WORKDIR = True

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('path', nargs='?', default=None)
        parser.add_argument('-a', '--all', default=0, const=-1, nargs='?', type=int)
        parser.add_argument('-d', '--depth', nargs='?', type=int)

    def add_perms(self, args, lines, path):
        f = self.storage.get_file(path)
        #parent = f.parent()

        perms_s = ''
        for key, perms in f.perms.iteritems():
            #if not parent or not key in parent.perms or parent.perms[key] != perms:
            perms_s += '%s(%s) ' % (key, f.p2str(perms))

        if args.depth is not None and path.strip('/').count('/') >= args.depth:
            return

        if len(perms_s) != 0 or args.all < 0 or path.strip('/').count('/') < args.all:
            lines.append((path, perms_s))

    def cmd(self, args):
        lines = []
        if args.path is None:
            path = self.working_dir
        else:
            path = os.path.realpath(os.path.join(self.working_dir, args.path))

        if not os.path.exists(path):
            print >>sys.stderr, 'Error: Path "%s" does not exist.' % path
            return 1

        for root, directories, files in os.walk(path):
            path = root[len(self.storage.root):]

            self.add_perms(args, lines, path + '/')
            for filename in files:
                self.add_perms(args, lines, os.path.join(path, filename))

        for line in sorted(lines):
            path, perms = line
            parts = path.split('/')
            if path.endswith('/'):
                filename = parts[-2] + '/'
                depth = path.count('/') - 1
            else:
                filename = parts[-1]
                depth = path.count('/')
            print '%-40s %s' % (' |' * depth + '-' + filename, perms)


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


class DownloadAction(ViewAction):
    def get(self):
        # serve the file, delegate everything to to FileApp
        self.ctx.res = FileApp(self.ctx.file.get_realpath())
        self.ctx.res.cache_control(private=True)
        CONTENT_DISPOSITION.apply(self.ctx.res.headers, \
                inline=True, filename=self.ctx.file.get_name())


class ListAction(MediaListAction):
    IS_MEDIA = False


class CoreCleaner(ICleaner):
    def fsck(self):
        self.v1()
        self.invalid_paths = []
        for f in self.storage.iter_files():
            if f.path is None or f._get_confname() != File._get_confname(f):
                print "%s has an invalid path: %s." % (f._get_confname(), f.path)
                self.invalid_paths.append(f)
            else:
                if f.view in ["", "None"]:
                    f.view = None
                    f.save()
                    print "%s: fixed empty view." % f._get_confname()

    def v1(self):
        """
        Migration for the introduction of the +i permission
        """
        config = self.storage.get_config()
        if config.data['storage'].get('version', 0) > 0:
            return
        for f in self.storage.iter_files():
            for key in f.perms.keys():
                perms = f.perms[key]
                # directories with the LIST perm will also get the IN perm
                # so files inherit it
                if perms & File.PERM_LIST:
                    perms = perms | File.PERM_IN
                # remove LIST perm for files (does not make sense)
                if f.isfile() and perms & File.PERM_LIST:
                    perms = perms & File.PERM_LIST
                f.perms[key] = perms
            f.save()
        print 'Migrated storage to v1'
        config.data['storage']['version'] = 1
        config.save()

    def gc(self):
        for f in self.invalid_paths:
            self.remove(f)


class CorePlugin(Plugin):
    def init(self):
        self.register_cli_command('init', InitCmd)
        self.register_cli_command('tree', TreeCmd)
        self.register_cli_command('chmod', ChModCmd)
        self.register_cli_command('chview', ChViewCmd)

        self.register_web_view(
                View(object_type='file', name='raw'),
                DownloadAction, 1)
        self.register_web_view(
                View(object_type='directory', name='list', verbose_name='Detailed list'),
                ListAction, 0)

        self.register_hook('cleanup', CoreCleaner)
