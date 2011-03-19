# -*- coding: utf-8 -*-

# Copyright(C) 2011  Romain Bignon, Laurent Bachelier
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import sys
import os
import posixpath

from ass2m.plugin import Plugin
from ass2m.cmd import Command

from ass2m.routes import Route
from ass2m.server import Action
from paste.fileapp import FileApp


__all__ = ['CorePlugin']


class InitCmd(Command):
    DESCRIPTION = 'Initialize the current directory as working tree'
    WORKDIR = False

    def cmd(self, args):
        if self.ass2m.storage:
            print >>sys.stderr, 'Error: %s is already a working directory' % self.working_dir
            return 1

        self.ass2m.create(self.working_dir)
        print 'Ass2m working directory created.'

class TreeCmd(Command):
    DESCRIPTION = 'Display the working tree'
    WORKDIR = True

    def cmd(self, args):
        for root, directories, files in os.walk(self.working_dir):
            path = root[len(self.ass2m.root):]
            depth = path.count('/')
            f = self.ass2m.storage.get_file(path)
            parent = f.parent()

            perms_s = ''
            for key, perms in f.perms.iteritems():
                if not parent or not key in parent.perms or parent.perms[key] != perms:
                    perms_s += '%s(%s) ' % (key, f.p2str(perms))

            if len(perms_s) == 0:
                continue

            print '%-40s %s' % ('  ' * depth + path + '/', perms_s)

class PermsCmd(Command):
    DESCRIPTION = 'Change permissions of a path'

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('path')
        parser.add_argument('who')
        parser.add_argument('perms', nargs='?')
        parser.add_argument('-D', action='store_true')

    def cmd(self, args):
        if not os.path.exists(args.path):
            print >>sys.stderr, 'Error: Path "%s" does not exist.' % args.path
            return 1

        f = self.ass2m.storage.get_file_from_realpath(os.path.realpath(args.path))
        if not f:
            print >>sys.stderr, 'Error: Path "%s" is not in working directory.' % args.path
            return 1

        if '.' in args.who:
            t, who = args.who.split('.', 1)
            if t == 'u':
                if not self.ass2m.storage.user_exists(who):
                    print >>sys.stderr, 'Error: User "%s" does not exist.' % who
                    return 1
            elif t == 'g':
                print >>sys.stderr, 'Not implemented yet'
                return 1
            else:
                print >>sys.stderr, 'Error: "%s" is not a right kind of target.' % t
                return 1
        elif args.who != 'all':
            print >>sys.stderr, 'Error: "%s" is not a right target.' % args.who
            print >>sys.stderr, 'Only available ones: "u.<username>", "g.<group>", "all"'
            return 1

        if args.D:
            if args.who in f.perms:
                f.perms.pop(args.who)
                f.save()
                print 'Removed permissions for %s on %s.' % (args.who, f.path)
                return 0
            else:
                print >>sys.stderr, 'Error: %s does not have permissions on %s.' % (args.who, f.path)
                return 1

        if args.perms is None:
            print 'Permissions for %s on %s: %s' % (args.who, f.path, f.p2str(f.perms[args.who]))
            return 0

        perms = f.perms.get(args.who, 0)
        state = -1
        for l in args.perms:
            if l == '+': state = 1
            elif l == '-': state = 0
            else:
                try:
                    perm = f.str2p(l)
                except KeyError:
                    print >>sys.stderr, 'Error: Perm "%s" does not exist.' % l
                    return 1
                if state == 1:   perms |= perm
                elif state == 0: perms &= ~perm
                else:
                    perms = perm
                    state = 1

        f.perms[args.who] = perms
        f.save()
        print 'Permissions for %s on %s are now: %s' % (args.who, f.path, f.p2str(f.perms[args.who]))


class Ass2mFileApp(FileApp):
    def guess_type(self):
        # add UTF-8 by default to text content-types
        guess = FileApp.guess_type(self)
        content_type = guess[0]
        if content_type and "text/" in content_type and "charset=" not in content_type:
            content_type += "; charset=UTF-8"
        return (content_type, guess[1])


class DownloadAction(Action):
    def answer(self):
        # serve the file, delegate everything to to FileApp
        self.ctx.res = Ass2mFileApp(self.ctx.file.get_realpath())


class ListAction(Action):
    def answer(self):
        dirs = []
        files = []
        for filename in sorted(os.listdir(self.ctx.file.get_realpath())):
            f = self.ctx.ass2m.storage.get_file(posixpath.join('/', self.ctx.path, filename))
            if not self.ctx.user.has_perms(f, f.PERM_LIST):
                continue
            if os.path.isdir(os.path.join(self.ctx.file.get_realpath(), filename)):
                dirs.append(filename)
            else:
                files.append(filename)

        self.ctx.template_vars['dirs'] = dirs
        self.ctx.template_vars['files'] = files
        self.ctx.res.body = self.ctx.render('list.html')


class CorePlugin(Plugin):
    def init(self):
        self.register_cli_command('init', InitCmd)
        self.register_cli_command('tree', TreeCmd)
        self.register_cli_command('perms', PermsCmd)

        self.register_web_action(
            Route(object_type = "file", action="download"),
            DownloadAction)

        self.register_web_action(
            Route(object_type = "directory", action="list", view="html"),
            ListAction)
