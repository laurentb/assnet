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
from webob.exc import HTTPNotFound

from ass2m.plugin import Plugin
from ass2m.routes import View
from ass2m.server import ViewAction, FileApp


__all__ = ['WebsitePlugin']


class WebsiteAction(ViewAction):
    PAGENAME = 'index.html'

    def get(self):
        path = os.path.join(self.ctx.file.get_realpath(), self.PAGENAME)
        try:
            open(path, 'r')
        except IOError, e:
            raise HTTPNotFound('File %s not found: %s' % (self.PAGENAME, e))
        else:
            self.ctx.res = FileApp(path)


class WebsitePlugin(Plugin):
    def init(self):
        self.register_web_view(
                View(object_type='directory', name='website'),
                WebsiteAction)
