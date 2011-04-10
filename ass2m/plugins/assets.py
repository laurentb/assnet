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
import re

from ass2m.plugin import Plugin

from ass2m.server import Action, FileApp
from webob.exc import HTTPNotFound, HTTPPreconditionFailed


__all__ = ['AssetsPlugin']


class AssetAction(Action):
    SANITIZE_REGEXP = re.compile(r'\w+\.\w+')

    def get(self):
        filename = self.ctx.req.str_GET.get('file')
        if self.SANITIZE_REGEXP.match(filename):
            paths = [os.path.join(path, 'assets') for path in self.ctx.DATA_PATHS]
            for path in paths:
                realpath = os.path.join(path, filename)
                if os.path.isfile(realpath):
                    self.ctx.res = FileApp(realpath)
                    return
            self.ctx.res = HTTPNotFound()
        else:
            self.ctx.res = HTTPPreconditionFailed()


class AssetsPlugin(Plugin):
    def init(self):
        self.register_web_action('asset', AssetAction)
