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
from ass2m.cmd import Command, CommandParent


__all__ = ['ConfigPlugin']


class ResolveCmd(Command):
    DESCRIPTION = 'Get the absolute path of the configuration file'

    def cmd(self, args):
        try:
            config = ConfigCmdParent.get_config(self.storage, args.config_info)
        except GetConfigError, e:
            print >>sys.stderr, 'Error: %s' % e
            return 1
        print '%s => %s' % (config, os.path.join(self.storage.path, config._get_confname()))


class ListConfigCmd(Command):
    DESCRIPTION = 'Get all the values of a configuration'

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('section', nargs='?')

    def cmd(self, args):
        try:
            config = ConfigCmdParent.get_config(self.storage, args.config_info)
        except GetConfigError, e:
            print >>sys.stderr, 'Error: %s' % e
            return 1

        for sectionkey, section in config.data.iteritems():
            if args.section is None or sectionkey == args.section:
                for key, value in section.iteritems():
                    print "%s.%s=%s" % (sectionkey, key, value)


class GetConfigCmd(Command):
    DESCRIPTION = 'Get the value of a configuration entry'

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('section_key', metavar='SECTION.KEY')

    def cmd(self, args):
        try:
            config = ConfigCmdParent.get_config(self.storage, args.config_info)
        except GetConfigError, e:
            print >>sys.stderr, 'Error: %s' % e
            return 1

        if '.' not in args.section_key:
            print >>sys.stderr, 'You must provide a section and a key (SECTION.KEY).'
            return 1

        section, key = args.section_key.split('.')
        if not config.data[section].has_key(key):
            print >>sys.stderr, 'Error: %s is undefined.' % args.section_key
            return 2

        print config.data[section][key]


class SetConfigCmd(Command):
    DESCRIPTION = 'Set the value of a configuration entry'

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('section_key', metavar='SECTION.KEY')
        parser.add_argument('value')

    def cmd(self, args):
        try:
            config = ConfigCmdParent.get_config(self.storage, args.config_info)
        except GetConfigError, e:
            print >>sys.stderr, 'Error: %s' % e
            return 1

        if '.' not in args.section_key:
            print >>sys.stderr, 'You must provide a section and a key (SECTION.KEY).'
            return 1

        section, key = args.section_key.split('.')
        config.data[section][key] = args.value
        config.save()


class GetConfigError(Exception):
    pass


class ConfigCmdParent(CommandParent):
    DESCRIPTION = 'Interact with the stored configurations'

    @staticmethod
    def configure_parser(parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('-g', '--global', help='Use global configuration',
                action='store_const', const=('global', None), dest='config_info')
        group.add_argument('-f', '--file', help='Use a file\'s configuration',
                type=lambda v: ('file', v), metavar='FILEPATH', dest='config_info')
        group.add_argument('-u', '--user', help='Use an user\'s configuration',
                type=lambda v: ('user', v), metavar='USERNAME', dest='config_info')

    @staticmethod
    def get_config(storage, config_info):
        config_type, config_name = config_info
        if config_type == 'global':
            return storage.get_config()
        elif config_type == 'file':
            f = storage.get_file_from_realpath(os.path.realpath(config_name))
            if not f:
                raise GetConfigError('Path "%s" is not in working directory %s.' % (config_name, storage.root))
            return f
        elif config_type == 'user':
            u = storage.get_user(config_name)
            if not u or not u.exists:
                raise GetConfigError('User "%s" does not exist.' % config_name)
            return u

class ConfigPlugin(Plugin):
    def init(self):
        self.register_cli_command('config', ConfigCmdParent)
        self.register_cli_command('config', 'get',     GetConfigCmd)
        self.register_cli_command('config', 'list',    ListConfigCmd)
        self.register_cli_command('config', 'resolve', ResolveCmd)
        self.register_cli_command('config', 'set',     SetConfigCmd)
