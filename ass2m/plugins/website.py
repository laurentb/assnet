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
        # file unreable or does not exist
        if not os.access(path, os.R_OK):
            # file exists, thus is unreadable
            if os.access(path, os.F_OK):
                raise HTTPNotFound('File %s is unreadable.' % self.PAGENAME)
            raise HTTPNotFound('File %s does not exist.' % self.PAGENAME)
        self.ctx.res = FileApp(path)


class WebsiteView(View):
    def check_file(self, f):
        return os.path.exists(os.path.join(f.get_realpath(),
                WebsiteAction.PAGENAME))


class WebsitePlugin(Plugin):
    def init(self):
        self.register_web_view(
                WebsiteView(object_type='directory', name='website'),
                WebsiteAction)
