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


import argparse

from .storage import Storage
from .butt import Butt
from .version import VERSION, COPYRIGHT


__all__ = ['CLI']


class CLI(object):
    def __init__(self, working_dir):
        self.working_dir = working_dir
        self.parser = argparse.ArgumentParser(prog='asn')
        self.butt = Butt(parser=self.parser)

        self.parser.add_argument('-V', '--version', action='version',
                             version='%(prog)s ' + VERSION + ' ' + COPYRIGHT)

    def main(self, argv):
        # TODO use cmd.Cmd to have a REPL application when no command
        # is supplied.
        storage = Storage.lookup(self.working_dir)
        args = self.parser.parse_args(argv[1:])
        cmd = args.cmd(storage, self.working_dir, self.butt)
        try:
            return cmd.run(args)
        except KeyboardInterrupt:
            print 'Program killed by SIGINT'
            return 1
        except EOFError:
            return 0
