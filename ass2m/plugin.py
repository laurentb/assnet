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


from .cmd import CommandParent


__all__ = ['Plugin']


class Plugin(object):
    def __init__(self, butt):
        self.butt = butt

    def init(self):
        pass

    def deinit(self):
        pass

    def register_cli_command(self, *args):
        parser = self.butt.parser
        if not parser:
            # not a cli application, does not need to register a command.
            return

        names = args[:-1]
        cmd = args[-1]

        if isinstance(cmd, basestring):
            description = cmd
            cmd = CommandParent
        else:
            description = cmd.DESCRIPTION

        for name in names:
            # XXX hack to store and get the subparser object.
            if hasattr(parser, '_subparser_action'):
                subparsers = parser._subparser_action
            else:
                subparsers = parser.add_subparsers()
                parser._subparser_action = subparsers

            # XXX use this private member because argparse does not give any
            # public method to get a subparser.
            if name in subparsers._name_parser_map:
                parser = subparsers._name_parser_map[name]
            else:
                parser = subparsers.add_parser(name, help=description)

        cmd.configure_parser(parser)
        if hasattr(cmd, 'cmd'):
            parser.set_defaults(cmd=cmd)

    def register_web_action(self, *args, **kwargs):
        router = self.butt.router
        if not router:
            # not a web application, does not need to register an action.
            return

        router.register_action(*args, **kwargs)

    def register_web_view(self, *args, **kwargs):
        router = self.butt.router
        if not router:
            # not a web application, does not need to register an action.
            return

        router.register_view(*args, **kwargs)

    def register_hook(self, name, hook):
        self.butt.hooks[name].append(hook)
