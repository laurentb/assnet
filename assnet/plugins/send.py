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


import os
import sys
from subprocess import list2cmdline

from assnet.plugin import Plugin
from assnet.cmd import Command
from assnet.filters import quote_url
from assnet.template import build_url, build_root_url
from assnet.users import Anonymous


__all__ = ['SendPlugin']


class GetUrlCmd(Command):
    DESCRIPTION = 'Get an URL for a specific file and/or user.'

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('path', nargs='+')
        parser.add_argument('-u', '--user', metavar='USERNAME')
        parser.add_argument('-K', '--no-key',
                action='store_false', dest='use_key',
                help="Don't use the user's key")
        parser.add_argument('-H', '--http-auth',
                action='store_true',
                help="Use HTTP authentication (for downloaders for instance)")

    def cmd(self, args):
        root_url = build_root_url(self.storage)
        if not root_url:
            print >>sys.stderr, \
                    'The web URL of this working directory is unknown.'
            print >>sys.stderr, 'Try to open it on the web or set the', \
                    'web.root_url configuration entry.'
            return 2

        if args.user:
            if not self.storage.user_exists(args.user):
                print >>sys.stderr, \
                    'Error: user %s does not exists.' % args.user
                return None
            user = self.storage.get_user(args.user)
        else:
            user = Anonymous()

        if args.use_key and user.exists and user.key is None:
            print >>sys.stderr, \
                'Warning: user %s has no key.' % user.name, \
                'Use contacts genkey %s to create one.' % user.name

        for path in args.path:
            if not os.path.exists(path):
                print >>sys.stderr, 'Error: Path "%s" does not exist.' % path
                continue

            f = self.storage.get_file_from_realpath(os.path.realpath(path))
            if not f:
                print >>sys.stderr, \
                        'Error: Path "%s" is not in working directory.' % path
                continue

            if not user.has_perms(f, f.PERM_READ):
                if user.exists:
                    print >>sys.stderr, \
                        'Warning: user %s cannot read %s.' % (user.name, f.path), \
                        'Use chmod u.%s +r %s' % (user.name, \
                            list2cmdline([os.path.relpath(f.get_realpath())]))
                else:
                    print >>sys.stderr, \
                        'Warning: anonymous users cannot read %s.' % (f.path)

            print quote_url(build_url(root_url, f, user=user,
                use_key=args.use_key, http_auth=args.http_auth))


class SendPlugin(Plugin):
    def init(self):
        self.register_cli_command('geturl', GetUrlCmd)
