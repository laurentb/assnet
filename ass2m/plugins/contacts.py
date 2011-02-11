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

from ass2m.plugin import Plugin
from ass2m.cmd import Command
from ass2m.users import User

class ContactsAddCmd(Command):
    DESCRIPTION = 'Add a contact'
    WORKDIR = True

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('username')

    def cmd(self, args):
        if self.ass2m.storage.user_exists(args.username):
            print >>sys.stderr, 'Error: user %s already exists.' % args.username
            return 1
        user = User(self.ass2m.storage, args.username)
        user.realname = self.ask('Enter the realname')
        user.email = self.ask('Enter the email address')
        user.save()
        print 'User %s correctly added.' % user.name

class ContactsListCmd(Command):
    DESCRIPTION = 'List contacts'
    WORKDIR = True

    def cmd(self, args):
        for user in self.ass2m.storage.iter_users():
            print '* %s: %s <%s>' % (user.name, user.realname, user.email)

class ContactsRemoveCmd(Command):
    DESCRIPTION = 'Remove a contact'
    WORKDIR = True

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('username')

    def cmd(self, args):
        if not self.ass2m.storage.user_exists(args.username):
            print >>sys.stderr, 'Error: user %s does not exist.' % args.username
            return 1

        self.ass2m.storage.remove_user(args.username)
        print 'User %s has been removed.' % args.username

class ContactsPlugin(Plugin):
    def __init__(self, ass2m):
        self.ass2m = ass2m
        self.register_cli_command('contacts', 'Contacts management')
        self.register_cli_command('contacts', 'add', ContactsAddCmd)
        self.register_cli_command('contacts', 'list', ContactsListCmd)
        self.register_cli_command('contacts', 'remove', ContactsRemoveCmd)
