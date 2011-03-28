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
import getpass
import re


__all__ = ['ConsolePart', 'Command']


# TODO change name
class ConsolePart(object):
    # shell escape strings
    BOLD   = '[1m'
    NC     = '[0m'    # no color

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

        question += u': '

        correct = False
        while not correct:
            if masked:
                line = getpass.getpass(question)
            else:
                sys.stdout.write(question.encode('utf-8'))
                sys.stdout.flush()
                line = sys.stdin.readline()
                if len(line) == 0:
                    raise EOFError()
                else:
                    line = line.rstrip('\r\n')

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

class Command(ConsolePart):
    NAME = None
    DESCRIPTION = None
    ALIASES = ()
    WORKDIR = True

    def cmd(self, args):
        raise NotImplementedError()

    @staticmethod
    def configure_parser(parser):
        return

    def __init__(self, storage, working_dir):
        self.storage = storage
        self.working_dir = working_dir

    def run(self, args):
        if self.WORKDIR and not self.storage:
            print >>sys.stderr, 'Error: Not a ass2m working directory.'
            print >>sys.stderr, 'Please use "%s init"' % sys.argv[0]
            return 1

        return self.cmd(args)
