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
import re

from ass2m.plugin import Plugin
from ass2m.cmd import Command, ConsolePart
from ass2m.storage import Storage
from ass2m.users import User, Group
from ass2m.filters import quote_url

from ass2m.server import Action
from webob.exc import HTTPFound


__all__ = ['ContactsManagement', 'ContactsSelection', 'ContactsPlugin']


class ContactsManagement(ConsolePart):
    def __init__(self, storage, show_groups=True):
        self.storage = storage
        self.users = list(self.storage.iter_users())
        self.groupscfg = self.storage.get_groupscfg()
        self.groups = sorted(self.groupscfg.itervalues())

    def add_contact(self, username=None, interactive=True,
                            realname=None, email=None):
        try:
            if username is None:
                username = self.ask('Enter the username', regexp='^\w+$')

            if self.storage.user_exists(username):
                print >>sys.stderr, 'Error: user %s already exists.' % username
                return None
            user = User(self.storage, username)
            self.edit_contact(user, interactive=interactive,
                                realname=realname, email=email)
            self.users.append(user)
            print 'User %s correctly added.' % user.name
            return user
        except (EOFError, KeyboardInterrupt):
            return None

    def edit_contact_password(self, username):
        try:
            if not self.storage.user_exists(username):
                print >>sys.stderr, 'Error: user %s does not exists.' % username
                return None
            user = self.storage.get_user(username)
            password1 = self.ask('Enter the new password', masked=True)
            password2 = self.ask('Confirm the new password', masked=True)
            if len(password1) == 0:
                return None
            if password1 != password2:
                print >>sys.stderr, 'Sorry, passwords do not match.'
                return None
            user.password = password1
            user.save()
            print 'Password of user %s changed.' % user.name
            return user
        except (EOFError, KeyboardInterrupt):
            return None

    def generate_contact_key(self, username):
        if not self.storage.user_exists(username):
            print >>sys.stderr, 'Error: user %s does not exists.' % username
            return None
        user = self.storage.get_user(username)
        user.gen_key()
        user.save()
        print 'Key of user %s set to %s.' % (user.name, user.key)
        return user

    def edit_contact(self, user, interactive=True, realname=None, email=None):
        if interactive:
            user.realname = self.ask('Enter the real name', default=user.realname or realname)
        elif realname:
            user.realname = realname
        if interactive:
            user.email = self.ask('Enter the email address', default=user.email or email, regexp='^[^ ]+@[^ ]+$')
        elif email:
            user.email = email
        user.save()

    def add_group(self, name=None):
        try:
            if name is None:
                name = self.ask('Enter the group name', regexp='^\w+$')

            if name in self.groupscfg:
                print >>sys.stderr, 'Error: group %s already exists.' % name
                return None

            group = Group(name)
            self.groups.append(group)
            self.groupscfg[name] = group

            self.edit_group(group)
            print 'Group %s correctly added.' % group.name
            return group
        except (EOFError, KeyboardInterrupt):
            return None

    def edit_group(self, group):
        cs = ContactsSelection(self.storage, group.users)
        cs.main()
        group.users = cs.sel_users
        self.groupscfg.save()

    def main(self):
        r = ''
        while r != 'q':
            print ''
            print 'Contacts:'
            self.print_users(1)
            print '%s a)%s --add contact--' % (self.BOLD, self.NC)
            print 'Groups:'
            self.print_groups(len(self.users) + 1)
            print '%s g)%s --add group--' % (self.BOLD, self.NC)
            try:
                self.print_extra_commands()
                print '%s q)%s --stop--' % (self.BOLD, self.NC)
                print ''
                r = self.print_menu()
            except (KeyboardInterrupt, EOFError):
                break

            if r.isdigit():
                i = int(r) - 1
                if i >= 0 and i < len(self.users):
                    user = self.users[i]
                    self.select_user(user)
                else:
                    i -= len(self.users)
                    if i >= 0 and i < len(self.groups):
                        group = self.groups[i]
                        self.select_group(group)
                    else:
                        print >>sys.stderr, 'Error: %s is not a valid choice' % r
                        continue
            elif r == 'a':
                self.add_contact()
            elif r == 'g':
                self.add_group()
            else:
                self.handle_extra_command(r)

    def select_user(self, user):
        self.edit_contact(user)

    def select_group(self, group):
        self.edit_group(group)

    def print_extra_commands(self):
        pass

    def handle_extra_command(self, r):
        pass

    def print_menu(self):
        return self.ask('Select a contacts to edit (or q to stop)',
                        regexp='^(\d+|q|a|g)$')

    def print_groups(self, start=1):
        for i, group in enumerate(self.storage.get_groupscfg().itervalues()):
            self.print_group(i + start, group)

    def print_group(self, i, group):
        desc = group.description
        if len(desc) > 30:
            desc = desc[:28] + '..'
        print '%s%2d)%s %s%-20s%s %-4s %s' % (self.BOLD, i, self.NC,
                                              self.BOLD, group.name, self.NC,
                                              ('(%d)' % len(group.users)), desc)

    def print_users(self, start=1):
        for i, user in enumerate(self.users):
            self.print_user(i + start, user)

    def print_user(self, i, user):
        print '%s%2d)%s %s%-20s%s "%s <%s>"' % (self.BOLD, i, self.NC,
                                                self.BOLD, user.name, self.NC,
                                                user.realname, user.email)


class ContactsSelection(ContactsManagement):
    def __init__(self, storage, sel_users=[], sel_groups=None):
        ContactsManagement.__init__(self, storage)
        self.sel_users = set(sel_users)
        self.sel_groups = set(sel_groups) if sel_groups is not None else None

    def print_menu(self):
        return self.ask('Select a contacts to check/uncheck (or q to stop)',
                        regexp='^(\d+|q|a|g|c|q)$')

    def print_extra_commands(self):
        print '%s c)%s --clear--' % (self.BOLD, self.NC)

    def handle_extra_command(self, r):
        if r == 'c':
            self.sel_users = []
            if self.sel_groups is not None:
                self.sel_groups = []

    def print_user(self, i, user):
        checked = 'x' if user.name in self.sel_users else ' '
        print '%s%2d)%s [%s] %s%-20s%s "%s <%s>"' % (self.BOLD, i, self.NC, checked,
                                                     self.BOLD, user.name, self.NC,
                                                     user.realname, user.email)

    def print_group(self, i, group):
        if self.sel_groups is None:
            status = '---'
            for user in group.users:
                if not user in self.sel_users:
                    status = '+++'
                    break
        else:
            status = '[x]' if group.name in self.sel_groups else '[ ]'
        desc = group.description
        if len(desc) > 30:
            desc = desc[:28] + '..'
        print '%s%2d)%s %s %s%-20s%s %-4s %s' % (self.BOLD, i, self.NC, status,
                                                 self.BOLD, group.name, self.NC,
                                                 ('(%d)' % len(group.users)), desc)

    def select_user(self, user):
        if user.name in self.sel_users:
            self.sel_users.remove(user.name)
        else:
            self.sel_users.add(user.name)

    def select_group(self, group):
        if self.sel_groups is None:
            cmd = self.sel_users.remove
            for user in group.users:
                if not user in self.sel_users:
                    cmd = self.sel_users.add

            for user in group.users:
                cmd(user)
            return

        if group.name in self.sel_groups:
            self.sel_groups.remove(group.name)
        else:
            self.sel_groups.add(group.name)


class ContactsAddCmd(Command):
    DESCRIPTION = 'Add a contact'

    @staticmethod
    def configure_parser(parser):
        # TODO validate arguments like in ContactsManagement
        parser.add_argument('username', nargs='?')
        parser.add_argument('-e', '--email', nargs='?')
        parser.add_argument('-r', '--realname', nargs='?')

    def cmd(self, args):
        cm = ContactsManagement(self.storage)
        if not cm.add_contact(args.username,
                interactive=not (args.email and args.realname),
                email=args.email, realname=args.realname):
            return 1


class ContactsEditCmd(Command):
    DESCRIPTION = 'Edit a contact'

    @staticmethod
    def configure_parser(parser):
        # TODO validate arguments like in ContactsManagement
        parser.add_argument('username')
        parser.add_argument('-e', '--email', nargs='?')
        parser.add_argument('-r', '--realname', nargs='?')

    def cmd(self, args):
        if not self.storage.user_exists(args.username):
            print >>sys.stderr, 'Error: user %s does not exist.' % args.username
            return 1
        user = self.storage.get_user(args.username)
        cm = ContactsManagement(self.storage)
        if not cm.edit_contact(user,
                interactive=not (args.email or args.realname),
                email=args.email, realname=args.realname):
            return 1


class ContactsPasswordCmd(Command):
    DESCRIPTION = 'Change the password of a contact'

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('username')

    def cmd(self, args):
        cm = ContactsManagement(self.storage)
        if not cm.edit_contact_password(args.username):
            return 1


class ContactsGenKeyCmd(Command):
    DESCRIPTION = 'Create or reset the key on a contact'

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('username')

    def cmd(self, args):
        cm = ContactsManagement(self.storage)
        if not cm.generate_contact_key(args.username):
            return 1


class ContactsMenuCmd(Command):
    DESCRIPTION = 'Display the contacts menu'

    def cmd(self, args):
        cm = ContactsManagement(self.storage)
        cm.main()


class ContactsMergeCmd(Command):
    DESCRIPTION = 'Merge contacts from another working directory'

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('workdir')

    def cmd(self, args):
        storage = Storage.lookup(args.workdir)
        if not storage:
            print >>sys.stderr, 'Error: Path "%s" is not a working directory' % args.workdir
            return 1

        for user in storage.iter_users():
            user.storage = self.storage
            user._old_data = None
            user.save()
            print 'Imported %s (%s <%s>)' % (user.name, user.realname, user.email)


class ContactsListCmd(Command):
    DESCRIPTION = 'List contacts'
    WORKDIR = True

    def cmd(self, args):
        cm = ContactsManagement(self.storage)
        cm.print_users()


class ContactsRemoveCmd(Command):
    DESCRIPTION = 'Remove a contact'
    WORKDIR = True

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('username')

    def cmd(self, args):
        if not self.storage.user_exists(args.username):
            print >>sys.stderr, 'Error: user %s does not exist.' % args.username
            return 1

        self.storage.get_user(args.username).remove()
        print 'User %s has been removed.' % args.username


class LoginAction(Action):
    FORM_RE = re.compile('login\[(\w+)\]')

    def _get_form(self):
        form = dict([(self.FORM_RE.match(k).groups()[0], v) \
                            for k, v in self.ctx.req.str_POST.iteritems() \
                            if self.FORM_RE.match(k)])
        form['referer'] = form.get('referer') \
                or self.ctx.req.referer \
                or quote_url(self.ctx.root_url)
        return form

    def get(self, form=None):
        form = form or self._get_form()
        self.ctx.template_vars['form'] = form
        self.ctx.res.body = self.ctx.render('login.html')

    def post(self):
        form = self._get_form()
        if form.get('username') and form.get('password'):
            user = self.ctx.storage.get_user(form['username'])
            if user and user.is_valid_password(form['password']):
                self.ctx.res = HTTPFound(location=form['referer'])
                # set cookie
                self.ctx.login(user)
                return
        self.get(form)


class LogoutAction(Action):
    def get(self):
        referer = self.ctx.req.referer or quote_url(self.ctx.root_url)
        self.ctx.res = HTTPFound(location=referer)
        self.ctx.logout()


class ContactsPlugin(Plugin):
    def init(self):
        self.register_cli_command('contacts', 'Contacts Management')
        self.register_cli_command('contacts', 'add', ContactsAddCmd)
        self.register_cli_command('contacts', 'edit', ContactsEditCmd)
        self.register_cli_command('contacts', 'genkey', ContactsGenKeyCmd)
        self.register_cli_command('contacts', 'list', ContactsListCmd)
        self.register_cli_command('contacts', 'menu', ContactsMenuCmd)
        self.register_cli_command('contacts', 'merge', ContactsMergeCmd)
        self.register_cli_command('contacts', 'password', ContactsPasswordCmd)
        self.register_cli_command('contacts', 'remove', ContactsRemoveCmd)

        self.register_web_action('login', LoginAction)
        self.register_web_action('logout', LogoutAction)
