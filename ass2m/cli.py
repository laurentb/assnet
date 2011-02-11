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
import getpass
import re

from ass2m import Ass2m, NotWorkingDir
from users import User

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
        print '    tree'
        print '    share PATH [CONTACTS..]'
        print '    contacts <add|list|remove>'

    @workdir
    def cmd_share(self, args):
        return

    @workdir
    def cmd_tree(self, args):
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

    @workdir
    def cmd_contacts(self, args):
        if len(args) < 1:
            print >>sys.stderr, 'Error: please give a command <list|add|remove>'
            return 1

        action = args[0]
        if action == 'list':
            for user in self.ass2m.storage.iter_users():
                print '* %s: %s <%s>' % (user.name, user.realname, user.email)
        elif len(args) < 2:
            print >>sys.stderr, 'Error: please give a username'
            return 1
        elif action == 'add':
            if self.ass2m.storage.user_exists(args[1]):
                print >>sys.stderr, 'Error: user %s already exists.' % args[1]
                return 1
            user = User(self.ass2m.storage, args[1])
            user.realname = self.ask('Enter the realname')
            user.email = self.ask('Enter the email address')
            user.save()
            print 'User %s correctly added.' % user.name
        elif action == 'remove':
            if not self.ass2m.storage.user_exists(args[1]):
                print >>sys.stderr, 'Error: user %s does not exist.' % args[1]
                return 1

            self.ass2m.storage.remove_user(args[1])
            print 'User %s has been removed.' % args[1]
        else:
            print >>sys.stderr, 'Error: Unknown command "%s"' % action
            return 1

        return 0

    def cmd_init(self, args):
        if self.ass2m:
            print >>sys.stderr, 'Error: %s is already a working directory' % os.getcwd()
            return 1

        self.ass2m = Ass2m.create(os.getcwd())
        print 'Ass2m working directory created.'

    def ask(self, question, default=None, masked=False, regexp=None, choices=None):
        """
        Ask a question to user.

        @param question  text displayed (str)
        @param default  optional default value (str)
        @param masked  if True, do not show typed text (bool)
        @param regexp  text must match this regexp (str)
        @return  entered text by user (str)
        """

        is_bool = False

        if choices:
            question = u'%s (%s)' % (question, '/'.join(
                [s for s in (choices.iterkeys() if isinstance(choices, dict) else choices)]))
        if default is not None:
            if isinstance(default, bool):
                question = u'%s (%s/%s)' % (question, 'Y' if default else 'y', 'n' if default else 'N')
                choices = ('y', 'n', 'Y', 'N')
                default = 'y' if default else 'n'
                is_bool = True
            else:
                question = u'%s [%s]' % (question, default)

        if masked:
            question = u'%s (hidden input)' % question

        question += ': '

        correct = False
        while not correct:
            line = getpass.getpass(question) if masked else raw_input(question)
            if not line and default is not None:
                line = default
            if isinstance(line, str):
                line = line.decode('utf-8')
            correct = (not regexp or re.match(unicode(regexp), unicode(line))) and \
                      (not choices or unicode(line) in
                       [unicode(s) for s in (choices.iterkeys() if isinstance(choices, dict) else choices)])

        if is_bool:
            return line.lower() == 'y'
        else:
            return line
