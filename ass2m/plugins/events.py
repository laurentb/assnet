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

from __future__ import with_statement

import re
import os
import sys
from datetime import datetime

from ass2m.plugin import Plugin
from ass2m.cmd import Command

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
        with open(self.f.get_disk_path(), 'w') as fp:
            self.print_me(fp)

    def print_me(self, fp):
        def binary(s):
            return unicode(s).encode('utf-8')

        fp.write('%s\n' % binary(self.title))
        fp.write('%s\n\n' % ('-' * len(unicode(self.title))))
        fp.write('%s\n\n' % binary(self.summary))
        fp.write('Date:\n')
        fp.write('%s\n\n' % (self.date.strftime('%Y-%m-%d %H:%M') if self.date else '1970-01-01 10:10'))
        fp.write('Place:\n')
        fp.write('%s\n\n' % binary(self.place))
        fp.write('Attendees:\n')
        stats = [0, 0, 0]
        for username, state in sorted(self.users.items()):
            realname = self.f.storage.get_user(username).realname
            checked = dict([(v, k) for k, v in self.STATES.iteritems()])[state]
            stats[state] += 1
            fp.write('[%s] %s (%s)\n' % (checked, binary(username), binary(realname)))
        fp.write('-- %d confirmed, %d waiting, %d declined\n' % (stats[0], stats[1], stats[2]))

    def load(self):
        (READ_TITLE,
         READ_SUMMARY,
         READ_FIELD_TITLE,
         READ_DATE,
         READ_PLACE,
         READ_ATTENDEES) = range(6)

        with open(self.f.get_disk_path(), 'r') as fp:
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

class EventCmd(Command):
    DESCRIPTION = 'Create or edit an event'
    WORKDIR = True

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('filename')

    def cmd(self, args):
        f = self.ass2m.storage.get_disk_file(args.filename)
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

                self.edit_event(event)
                event.print_me(sys.stdout)

                if self.ask('Do you want to save this event?', default=True):
                    event.save()
                else:
                    os.unlink(f.get_disk_path())
            return 0

        event.print_me(sys.stdout)
        event.save()

    def edit_event(self, event):
        event.title = self.ask('Title')
        event.summary = self.ask('Enter the summary of the event')
        while not event.date:
            date = self.ask('Enter date (yyyy-mm-dd hh:ss)')
            try:
                event.date = datetime.strptime(date, '%Y-%m-%d %H:%M')
            except ValueError, v:
                print >>sys.stderr, 'Error: %s' % v
        event.place = self.ask('Enter a place')

class EventsPlugin(Plugin):
    def init(self):
        self.register_cli_command('event', EventCmd)
