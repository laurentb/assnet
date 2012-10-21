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


import re
import os
import sys
from textwrap import wrap
from datetime import datetime

from ass2m.plugin import Plugin
from ass2m.routes import View
from ass2m.server import ViewAction
from ass2m.cmd import Command
from ass2m.template import build_url, build_root_url
from ass2m.mail import Mail

from .contacts import ContactsSelection
from .cleanup import ICleaner


__all__ = ['EventsPlugin']


class Event(object):
    (USER_CONFIRMED,
     USER_MAYBE,
     USER_WAITING,
     USER_DECLINED) = range(4)

    STATES = {'x': USER_CONFIRMED,
              '?': USER_MAYBE,
              ' ': USER_WAITING,
              '-': USER_DECLINED
             }

    STATES_LABEL = {USER_CONFIRMED: 'confirmed',
                    USER_MAYBE:     'maybe',
                    USER_WAITING:   'waiting',
                    USER_DECLINED:  'declined',
                   }

    def __init__(self, f):
        self.f = f
        self.title = None
        self.summary = None
        self.date = None
        self.place = None
        self.users = {}
        self.users_to_notify = set()

    def save(self):
        with open(self.f.get_realpath(), 'w') as fp:
            self._print(fp)

        self.f.clear_user_perms()
        for username in self.users.iterkeys():
            self.f.set_user_perms(username, self.f.PERM_WRITE |
                                            self.f.PERM_READ |
                                            self.f.PERM_LIST |
                                            self.f.PERM_IN)
        self.f.mimetype = 'text/event'
        self.f.save()

        self.send()

    def send(self):
        """
        Send mails to new users.
        """
        mails = set()
        while len(self.users_to_notify) > 0:
            mail = self.send_email(self.users_to_notify.pop())
            if mail:
                mails.add(mail)

        self.users_to_notify.clear()
        return mails

    def send_email(self, username):
        user = self.f.storage.get_user(username)
        if not user.exists:
            return

        if not user.key:
            user.gen_key()
            user.save()
        url = build_url(build_root_url(self.f.storage),
                        self.f, user=user, use_key=True)
        mail = user.new_mail('event-notification.mail', 'Notification of event')
        mail.vars['realname'] = user.realname
        mail.vars['description'] = self.summary
        mail.vars['url'] = url
        mail.send()
        return user.email

    def notify_state_changed(self, user):
        config = self.f.storage.get_config()
        if not 'sender' in config.data['mail']:
            return

        sender = config.data['mail']['sender']
        recipient = config.data['mail']['sender']
        smtp = config.data['mail'].get('smtp', 'localhost')
        subject = 'A user has changed state'

        mail = Mail(self.f.storage, 'event-state-changed.mail', sender, recipient, subject, smtp)
        mail.vars['realname'] = user.realname
        mail.vars['state'] = self.STATES_LABEL[self.users[user.name]]
        mail.vars['url'] = build_url(build_root_url(self.f.storage), self.f)
        mail.send()

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
        stats = [0, 0, 0, 0]
        for username, state in sorted(self.users.items(), key=lambda (k, v): (v, k)):
            realname = self.get_user(username).realname
            checked = self.get_sign(state)
            stats[state] += 1
            fp.write('[%s] %s (%s)\n' % (checked, binary(username), binary(realname)))
        fp.write('-- %d confirmed, %d maybe, %d waiting, %d declined\n' % (stats[0], stats[1], stats[2], stats[3]))

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
            yield self.get_user(username)

    def get_user(self, username):
        return self.f.storage.get_user(username, want_fake=True)

    def remove_user(self, username):
        self.users.pop(username)
        self.users_to_notify.discard(username)

    def add_user(self, username):
        self.users[username] = self.USER_WAITING
        self.users_to_notify.add(username)


class EventsCmd(Command):
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
                    print >>sys.stderr, 'Unable to save: %s' % e
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
            except (KeyboardInterrupt, EOFError):
                print '\nAborted.'
            else:
                event.print_me()
                self.save_event(event)

    def edit_event(self, event):
        self.edit_title(event)
        self.edit_summary(event)
        self.edit_date(event)
        self.edit_place(event)
        self.edit_attendees(event)
        event.print_me()
        if self.ask('Do you want to save this event?', default=True):
            self.save_event(event)

    def save_event(self, event):
        try:
            event.save()
        except IOError, e:
            print >>sys.stderr, 'Unable to save: %s' % e
            return 1
        try:
            mails = []
            mails = event.send()
        except IOError, e:
            print >>sys.stderr, 'Unable to send mails: %s' % e
            return 1
        if mails:
            print 'Mails sent to %s' % ', '.join(mails)

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
        for deleted in (set(event.users.keys()) - cs.sel_users):
            event.remove_user(deleted)
        for added in cs.sel_users - set(event.users.keys()):
            event.add_user(added)


class EventAction(ViewAction):
    def get(self, state=None):
        user_state = None
        error_message = None
        confirm_message = None

        event = Event(self.ctx.file)
        try:
            event.load()
        except IOError, e:
            error_message = unicode(e)

        if self.ctx.user.exists and \
                self.ctx.user.has_perms(event.f, event.f.PERM_WRITE) and \
                self.ctx.user.name in event.users:
            if state is not None:
                event.users[self.ctx.user.name] = state

                try:
                    event.save()
                except IOError, e:
                    error_message = unicode(e)
                    event.load()
                else:
                    confirm_message = 'Your state has been changed!'
                    event.notify_state_changed(self.ctx.user)

            user_state = event.users[self.ctx.user.name]

        self.ctx.template_vars['event'] = event
        self.ctx.template_vars['user_state'] = user_state
        self.ctx.template_vars['error_message'] = error_message
        self.ctx.template_vars['confirm_message'] = confirm_message
        self.ctx.template_vars['stylesheets'].append('event.css')
        self.ctx.res.body = self.ctx.render('event.html')

    def delete(self):
        self.get(Event.USER_DECLINED)

    def put(self):
        state = self.ctx.req.POST.get('_state')
        if state == 'maybe':
            self.get(Event.USER_MAYBE)
        else:
            self.get(Event.USER_CONFIRMED)


class EventsCleaner(ICleaner):
    def fsck(self):
        for f in self.storage.iter_files():
            # update new way to know the file is an event
            if f.view == 'event':
                f.mimetype = 'text/event'
                # not needed anymore, the default view will be the most precise
                f.view = None
                f.save()
                print "%s updated to a newer Event config." % f.path

    def gc(self):
        pass


class EventsPlugin(Plugin):
    def init(self):
        self.register_cli_command('events', EventsCmd)
        self.register_web_view(
            View(object_type='file', mimetype='text/event', name='event'),
            EventAction)
        self.register_hook('cleanup', EventsCleaner)
