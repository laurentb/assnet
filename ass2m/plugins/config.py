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

import os
import sys

from ass2m.plugin import Plugin
from ass2m.cmd import Command


__all__ = ['ConfigPlugin']


class ResolveCmd(Command):
    DESCRIPTION = 'Get the storage name of a path'

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('path', nargs='+')

    def cmd(self, args):
        for path in args.path:
            if not os.path.exists(path):
                print >>sys.stderr, 'Error: Path "%s" does not exist.' % path
                continue

            f = self.storage.get_file_from_realpath(os.path.realpath(path))
            if not f:
                print >>sys.stderr, 'Error: Path "%s" is not in working directory.' % path
                continue
            print '%s => %s' % (f.path, os.path.join(self.storage.path, f._get_confname()))


class ListConfigCmd(Command):
    DESCRIPTION = 'Get all the values of the global config'

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('section', nargs='?')

    def cmd(self, args):
        config = self.storage.get_config()
        self._print_config(config.data, args.section)

    def _print_config(self, data, filter_section = None):
        for sectionkey, section in data.iteritems():
            if filter_section is None or sectionkey == filter_section:
                for key, value in section.iteritems():
                    print "%s.%s=%s" % (sectionkey, key, value)


class ConfigPlugin(Plugin):
    def init(self):
        self.register_cli_command('config', 'Interact with the stored configurations')
        self.register_cli_command('config', 'resolve', ResolveCmd)
        self.register_cli_command('config', 'global', 'Interact with the global configuration')
        self.register_cli_command('config', 'global', 'list', ListConfigCmd)
