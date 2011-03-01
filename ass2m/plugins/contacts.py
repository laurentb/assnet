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
from copy import copy

from ass2m import Ass2m
from ass2m.plugin import Plugin
from ass2m.cmd import Command, ConsolePart
from ass2m.users import User

from ass2m.routes import Route
from ass2m.server import Action
from paste.auth.cookie import AuthCookieSigner
from webob import html_escape

__all__ = ['ContactsManagement', 'ContactsSelection']


class ContactsManagement(ConsolePart):
    def __init__(self, ass2m):
        self.ass2m = ass2m
        self.users = list(self.ass2m.storage.iter_users())

    def add_contact(self, username=None):
        try:
            if username is None:
                username = self.ask('Enter the username', regexp='^\w+$')

            if self.ass2m.storage.user_exists(username):
                print >>sys.stderr, 'Error: user %s already exists.' % username
                return None
            user = User(self.ass2m.storage, username)
            self.edit_contact(user)
            self.users.append(user)
            print 'User %s correctly added.' % user.name
            return user
        except (EOFError,KeyboardInterrupt):
            return None

    def edit_contact(self, user):
        user.realname = self.ask('Enter the realname', default=user.realname)
        user.email = self.ask('Enter the email address', default=user.email, regexp='^[^ ]+@[^ ]+$')
        user.save()

    def main(self):
        r = ''
        while r != 'q':
            print ''
            print 'Contacts:'
            self.print_users()
            try:
                print '%s a)%s --add--' % (self.BOLD, self.NC)
                print '%s q)%s --stop--' % (self.BOLD, self.NC)
                print ''
                r = self.print_menu()
            except (KeyboardInterrupt,EOFError):
                break

            if r.isdigit():
                i = int(r) - 1
                if i < 0 or i >= len(self.users):
                    print >>sys.stderr, 'Error: %s is not a valid choice' % r
                    continue
                user = self.users[i]
                self.select_user(user)
            elif r == 'a':
                self.add_contact()

    def select_user(self, user):
        self.edit_contact(user)

    def print_menu(self):
        return self.ask('Select a contacts to edit (a to add one, or q to stop)',
                        regexp='^(\d+|q|a)$')

    def print_users(self):
        users = list(self.ass2m.storage.iter_users())
        for i, user in enumerate(users):
            self.print_user(i, user)

    def print_user(self, i, user):
        print '%s%2d)%s %s%-15s%s  "%s <%s>"' % (self.BOLD, i+1, self.NC,
                                                 self.BOLD, user.name, self.NC,
                                                 user.realname, user.email)

class ContactsSelection(ContactsManagement):
    def __init__(self, ass2m, sel_users=[], sel_groups=[]):
        ContactsManagement.__init__(self, ass2m)
        self.sel_users = copy(sel_users)
        self.sel_groups = copy(sel_groups)

    def print_menu(self):
        return self.ask('Select a contacts to check/uncheck (a to add one, or q to stop)',
                        regexp='^(\d+|q|a)$')

    def print_user(self, i, user):
        checked = 'x' if user.name in self.sel_users else ' '
        print '%s%2d)%s [%s] %s%-15s%s  "%s <%s>"' % (self.BOLD, i+1, self.NC, checked,
                                                      self.BOLD, user.name, self.NC,
                                                      user.realname, user.email)

    def select_user(self, user):
        if user.name in self.sel_users:
            self.sel_users.remove(user.name)
        else:
            self.sel_users.append(user.name)

class ContactsAddCmd(Command):
    DESCRIPTION = 'Add a contact'

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('username')

    def cmd(self, args):
        cm = ContactsManagement(self.ass2m)
        if not cm.add_contact(args.username):
            return 1

class ContactsMenuCmd(Command):
    DESCRIPTION = 'Display the contacts menu'

    def cmd(self, args):
        cm = ContactsManagement(self.ass2m)
        cm.main()

class ContactsMergeCmd(Command):
    DESCRIPTION = 'Merge contacts from another working directory'

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('workdir')

    def cmd(self, args):
        ass2m = Ass2m(args.workdir)
        if not ass2m.storage:
            print >>sys.stderr, 'Error: Path "%s" is not a working directory' % args.workdir
            return 1

        for user in ass2m.storage.iter_users():
            user.storage = self.ass2m.storage
            user.save()
            print 'Imported %s (%s <%s>)' % (user.name, user.realname, user.email)

class ContactsListCmd(Command):
    DESCRIPTION = 'List contacts'
    WORKDIR = True

    def cmd(self, args):
        cm = ContactsManagement(self.ass2m)
        cm.print_users()

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


class LoginAction(Action):
    def answer(self):
        signer = AuthCookieSigner(secret=self.ctx.cookie_secret)
        form_user = self.ctx.req.str_POST.get('user')
        if form_user:
            # set cookie
            cookie = signer.sign(form_user)
            self.ctx.res.set_cookie('ass2m_auth', cookie)

            self.ctx.user = self.ctx.ass2m.storage.get_user(form_user)

        self.ctx.res.body = """<html><body>Current user: %s<br/>
                        <form method="post"><label>Username</label><input name="user" />
                        <input type="submit" /></form>
                        </body></html>""" % html_escape(str(self.ctx.user))

        return self.ctx.wsgi_response()


class ContactsPlugin(Plugin):
    def init(self):
        self.register_cli_command('contacts', 'Contacts Management')
        self.register_cli_command('contacts', 'add', ContactsAddCmd)
        self.register_cli_command('contacts', 'merge', ContactsMergeCmd)
        self.register_cli_command('contacts', 'menu', ContactsMenuCmd)
        self.register_cli_command('contacts', 'list', ContactsListCmd)
        self.register_cli_command('contacts', 'remove', ContactsRemoveCmd)

        self.register_web_action(
            Route(object_type = None, action="login"),
            LoginAction)
        self.register_web_action(
            Route(object_type = None, action="login", method="POST"),
            LoginAction)
