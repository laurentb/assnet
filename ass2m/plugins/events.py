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

from __future__ import with_statement

import re
import os
import sys
from textwrap import wrap
from datetime import datetime

from ass2m.plugin import Plugin
from ass2m.routes import Route
from ass2m.server import Action
from ass2m.cmd import Command

from .contacts import ContactsSelection


__all__ = ['EventsPlugin']


class Event(object):
    (USER_CONFIRMED,
     USER_WAITING,
     USER_DECLINED) = range(3)

    STATES = {'x': USER_CONFIRMED,
              ' ': USER_WAITING,
              '-': USER_DECLINED
             }

    def __init__(self, f):
        self.f = f
        self.title = None
        self.summary = None
        self.date = None
        self.place = None
        self.users = {}

    def save(self):
        with open(self.f.get_realpath(), 'w') as fp:
            self._print(fp)

        self.f.clear_user_perms()
        for username in self.users.iterkeys():
            self.f.set_user_perms(username, self.f.PERM_WRITE|
                                            self.f.PERM_READ|
                                            self.f.PERM_LIST)
        self.f.view = 'event'
        self.f.save()

    def print_me(self):
        print '-' * len(unicode(self.title))
        self._print(sys.stdout)
        print ''

    def _print(self, fp):
        def binary(s):
            return unicode(s).encode('utf-8')

        fp.write('%s\n' % binary(self.title))
        fp.write('%s\n\n' % ('-' * len(unicode(self.title))))
        fp.write('%s\n\n' % '\n'.join(wrap(binary(self.summary), 78)))
        fp.write('Date:\n')
        fp.write('%s\n\n' % (self.date.strftime('%Y-%m-%d %H:%M') if self.date else '1970-01-01 10:10'))
        fp.write('Place:\n')
        fp.write('%s\n\n' % binary(self.place))
        fp.write('Attendees:\n')
        stats = [0, 0, 0]
        for username, state in sorted(self.users.items(), key=lambda (k,v): (v,k)):
            realname = self.f.storage.get_user(username).realname
            checked = self.get_sign(state)
            stats[state] += 1
            fp.write('[%s] %s (%s)\n' % (checked, binary(username), binary(realname)))
        fp.write('-- %d confirmed, %d waiting, %d declined\n' % (stats[0], stats[1], stats[2]))

    def get_sign(self, state):
        return dict([(v, k) for k, v in self.STATES.iteritems()])[state]

    def load(self):
        (READ_TITLE,
         READ_SUMMARY,
         READ_FIELD_TITLE,
         READ_DATE,
         READ_PLACE,
         READ_ATTENDEES) = range(6)

        with open(self.f.get_realpath(), 'r') as fp:
            state = READ_TITLE
            for line in fp.xreadlines():
                line = line.strip().decode('utf-8')
                if state == READ_TITLE:
                    if self.title is None:
                        self.title = line
                    if not line:
                        state += 1
                elif state == READ_SUMMARY:
                    if not line:
                        state += 1
                    else:
                        if self.summary is not None:
                            self.summary += u'\n%s' % line
                        else:
                            self.summary = line
                elif state == READ_FIELD_TITLE:
                    if line == 'Date:':
                        state = READ_DATE
                    if line == 'Place:':
                        state = READ_PLACE
                    if line == 'Attendees:':
                        state = READ_ATTENDEES
                elif state == READ_DATE:
                    try:
                        self.date = datetime.strptime(line, '%Y-%m-%d %H:%M')
                    except ValueError, e:
                        print 'Warning: invalid datetime (%s)' % e
                    state = READ_FIELD_TITLE
                elif state == READ_PLACE:
                    self.place = line
                    state = READ_FIELD_TITLE
                elif state == READ_ATTENDEES:
                    m = re.match('^\[(.)\] ([^ ]+)', line)
                    if m:
                        self.users[m.group(2)] = self.STATES[m.group(1)]
                    else:
                        state = READ_FIELD_TITLE

    def iter_users(self):
        for username in sorted(self.users.keys(), key=unicode.lower):
            yield self.f.storage.get_user(username)

    def remove_user(self, username):
        self.users.pop(username)

    def add_user(self, username):
        self.users[username] = self.USER_WAITING

class EventCmd(Command):
    DESCRIPTION = 'Create or edit an event'
    WORKDIR = True

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('filename')

    def cmd(self, args):
        f = self.storage.get_file_from_realpath(args.filename)
        if not f:
            print >>sys.stderr, 'Error: file "%s" is not in the working tree.' % args.filename
            return 1

        event = Event(f)
        try:
            event.load()
        except IOError:
            if self.ask('Warning: Event %s does not exist. Do you want to create it?' % f.path, default=True):
                try:
                    event.save()
                except IOError, e:
                    print >>sys.stderr, 'Error: %s' % e
                    return 1

                os.unlink(f.get_realpath())
                self.edit_event(event)
            return 0

        r = ''
        event.print_me()
        while r != 'q':
            r = self.ask('Choose an action (t/s/d/p/a to edit, ? to get help, or q to exit)',
                         regexp='^(t|s|d|p|a|\?|q)$')
            try:
                if r == 't': self.edit_title(event)
                if r == 's': self.edit_summary(event)
                if r == 'd': self.edit_date(event)
                if r == 'p': self.edit_place(event)
                if r == 'a': self.edit_attendees(event)
                if r == '?':
                    print 't = edit title'
                    print 's = edit summary'
                    print 'd = edit date'
                    print 'p = edit place'
                    print 'a = edit attendees'
                    continue
                if r == 'q':
                    continue
            except (KeyboardInterrupt,EOFError):
                print '\nAborted.'
            else:
                event.save()
                event.print_me()

    def edit_event(self, event):
        self.edit_title(event)
        self.edit_summary(event)
        self.edit_date(event)
        self.edit_place(event)
        self.edit_attendees(event)
        event.print_me()
        if self.ask('Do you want to save this event?', default=True):
            event.save()

    def edit_title(self, event):
        event.title = self.ask('Title', default=event.title)

    def edit_summary(self, event):
        event.summary = self.ask('Enter the summary of the event', default=event.summary)

    def edit_date(self, event):
        while 1:
            date = self.ask('Enter date (yyyy-mm-dd hh:ss)',
                            default=(event.date.strftime('%Y-%m-%d %H:%M')
                                     if event.date else None))
            try:
                event.date = datetime.strptime(date, '%Y-%m-%d %H:%M')
            except ValueError, v:
                print >>sys.stderr, 'Error: %s' % v
            else:
                break

    def edit_place(self, event):
        event.place = self.ask('Enter a place', default=event.place)

    def edit_attendees(self, event):
        cs = ContactsSelection(self.storage, event.users.keys())
        cs.main()
        for deleted in (set(event.users.keys()) - set(cs.sel_users)):
            event.remove_user(deleted)
        for added in set(cs.sel_users) - set(event.users.keys()):
            event.add_user(added)

class EventAction(Action):
    def answer(self):
        user_state = None
        error_message = None
        confirm_message = None

        event = Event(self.ctx.file)
        try:
            event.load()
        except IOError, e:
            error_message = unicode(e)

        if self.ctx.user.has_perms(event.f, event.f.PERM_WRITE) and \
           self.ctx.user.name in event.users:
            form_action = self.ctx.req.str_POST.get('action')
            if form_action:
                if form_action == "Confirm":
                    event.users[self.ctx.user.name] = event.USER_CONFIRMED
                elif form_action == "Decline":
                    event.users[self.ctx.user.name] = event.USER_DECLINED

                try:
                    event.save()
                except IOError, e:
                    error_message = unicode(e)
                    event.load()
                else:
                    confirm_message = 'Your state has been changed!'

            user_state = event.users[self.ctx.user.name]

        self.ctx.template_vars['event'] = event
        self.ctx.template_vars['user_state'] = user_state
        self.ctx.template_vars['error_message'] = error_message
        self.ctx.template_vars['confirm_message'] = confirm_message
        self.ctx.template_vars['stylesheets'].append('event.css')
        self.ctx.res.body = self.ctx.render('event.html')

class EventsPlugin(Plugin):
    def init(self):
        self.register_cli_command('event', EventCmd)
        self.register_web_action(
            Route(object_type = "file", action="download", view="event"),
            EventAction)
        self.register_web_action(
            Route(object_type = "file", action="download", view="event", method="POST"),
            EventAction)
