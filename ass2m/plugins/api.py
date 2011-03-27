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

import json

from ass2m.plugin import Plugin

from ass2m.routes import Route
from ass2m.server import Action

__all__ = ['ApiPlugin']


class InfoAction(Action):
    def answer(self):
        self.ctx.res.content_type = 'application/json'
        self.ctx.res.body = json.dumps(self.get_fileinfo(self.ctx.file))

    def get_fileinfo(self, f):
        fileinfo = dict()
        if f.isdir():
            fileinfo['type'] = 'directory'
            fileinfo['size'] = None
        else:
            fileinfo['type'] = 'file'
            fileinfo['size'] = f.get_size()
        fileinfo['mtime'] = f.get_mtime().isoformat().split('.')[0]
        return fileinfo


class JsonListAction(InfoAction):
    def answer(self):
        files = dict()
        for f in self.ctx.iter_files():
            files[f.get_name()] = self.get_fileinfo(f)

        info = dict(files=files)

        self.ctx.res.content_type = 'application/json'
        self.ctx.res.body = json.dumps(info)


class TextListAction(Action):
    def answer(self):
        filenames = []
        for f in self.ctx.iter_files():
            if f.isdir():
                filenames.append(f.get_name()+'/')
            else:
                filenames.append(f.get_name())

        self.ctx.res.content_type = 'text/plain'
        self.ctx.res.charset = 'UTF-8'
        self.ctx.res.body = '\n'.join(filenames)


class ApiPlugin(Plugin):
    def init(self):
        self.register_web_action(
            Route(object_type = "file", action="info", view="json", public=False),
            InfoAction)

        self.register_web_action(
            Route(object_type = "directory", action="info", view="json", public=False),
            InfoAction)

        self.register_web_action(
            Route(object_type = "directory", action="list", view="json", public=False),
            JsonListAction)

        self.register_web_action(
            Route(object_type = "directory", action="list", view="text", public=False),
            TextListAction)
