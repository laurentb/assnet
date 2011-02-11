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


from .cmd import Command

class Plugin(object):
    def __init__(self, ass2m):
        self.ass2m = ass2m

    def register_cli_command(self, *args):
        parser = self.ass2m.parser
        if not parser:
            # not a cli application, does not need to register command.
            return

        names = args[:-1]
        cmd = args[-1]

        if isinstance(cmd, type) and issubclass(cmd, Command):
            description = cmd.DESCRIPTION
        else:
            description = cmd
            cmd = None

        for name in names:
            if hasattr(parser, '_subparser_action'):
                subparsers = parser._subparser_action
            else:
                subparsers = parser.add_subparsers()
                parser._subparser_action = subparsers

            if name in subparsers._name_parser_map:
                parser = subparsers._name_parser_map[name]
            else:
                parser = subparsers.add_parser(name, help=description)

        if cmd:
            cmd.configure_parser(parser)
            parser.set_defaults(cmd=cmd)
