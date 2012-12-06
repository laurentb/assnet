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


from assnet.plugin import Plugin
from assnet.cmd import Command


__all__ = ['CleanupPlugin', 'ICleaner']


class ICleaner(object):
    def __init__(self, storage):
        self.storage = storage

    def fsck(self):
        """
        Checks integrity, perform uprades.
        This is the required first part of a cleanup.
        It should avoid destroying information.
        """
        raise NotImplementedError()

    def gc(self):
        """
        Remove useless, outdated, invalid, etc. entries. This is optional.
        """
        raise NotImplementedError()

    def remove(self, obj):
        """
        Remove a storage object.
        Checks if it still exists before attempting, since
        it could have been deleted for another reason in the
        same cleanup run.
        """
        obj.read()
        if obj.exists:
            obj.remove()
            print "Removed %s." % obj._get_confname()


class CleanupCmd(Command):
    DESCRIPTION = 'Check and fix the assnet storage data'

    @staticmethod
    def configure_parser(parser):
        parser.add_argument('-g', '--gc', help='Run garbage collection', \
                                action='store_true', dest='gc')

    def cmd(self, args):
        cleaners = [cleaner(self.storage) \
                for cleaner in self.butt.hooks['cleanup']]
        for cleaner in cleaners:
            cleaner.fsck()
        if args.gc:
            for cleaner in cleaners:
                cleaner.gc()


class CleanupPlugin(Plugin):
    def init(self):
        self.register_cli_command('cleanup', CleanupCmd)
