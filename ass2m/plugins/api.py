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


import json

from ass2m.plugin import Plugin

from ass2m.routes import View
from ass2m.server import ViewAction

__all__ = ['ApiPlugin']


class InfoAction(ViewAction):
    def get_fileinfo(self, f):
        fileinfo = dict()
        if f.isdir():
            fileinfo['type'] = 'directory'
            fileinfo['size'] = None
        else:
            fileinfo['type'] = 'file'
            fileinfo['size'] = f.get_size()
        fileinfo['mtime'] = f.get_mtime().strftime(r'%Y-%m-%dT%H:%M:%S')
        return fileinfo


class JsonInfoAction(InfoAction):
    def get(self):
        self.ctx.res.content_type = 'application/json'
        self.ctx.res.body = json.dumps(self.get_fileinfo(self.ctx.file))


class JsonListAction(InfoAction):
    def get(self):
        files = dict()
        for f in self.ctx.iter_files():
            files[f.get_name()] = self.get_fileinfo(f)

        info = dict(files=files)

        self.ctx.res.content_type = 'application/json'
        self.ctx.res.body = json.dumps(info)


class TextListAction(ViewAction):
    def get(self):
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
        self.register_web_view(
            View(object_type=None, name='json_info', public=False, verbose_name='JSON info'),
            JsonInfoAction)

        self.register_web_view(
            View(object_type='directory', name='json_list', public=False, verbose_name='JSON list'),
            JsonListAction)

        self.register_web_view(
            View(object_type='directory', name='text_list', public=False, verbose_name='Text-only list'),
            TextListAction)
