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


import json
from dateutil import tz
import PyRSS2Gen
from mako.filters import html_escape

from assnet.plugin import Plugin

from assnet.routes import View
from assnet.server import ViewAction
from assnet.template import build_url, build_root_url

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
                filenames.append(f.get_name() + '/')
            else:
                filenames.append(f.get_name())

        self.ctx.res.content_type = 'text/plain'
        self.ctx.res.charset = 'UTF-8'
        self.ctx.res.body = '\n'.join(filenames)

class RssListAction(InfoAction):
    NB_ENTRIES = 20

    class SortableFile(object):
        def __init__(self, f):
            self.obj = f
            self.mtime = f.get_mtime().replace(tzinfo=tz.tzlocal()).astimezone(tz.tzutc())

        def __lt__(self, o):
            return self.mtime < o.mtime

    def get(self):
        base_dir = self.SortableFile(self.ctx.file)
        files = []
        for f in self.ctx.iter_files_recursively():
            if not f.isdir():
                files.append(self.SortableFile(f))
        files.sort(reverse=True)

        root_url = build_root_url(self.ctx.storage)
        items = []
        for f in files[:self.NB_ENTRIES]:
            link = build_url(root_url, f.obj, user=self.ctx.user)
            description = None
            mimetype = f.obj.get_mimetype()
            if mimetype is not None and self.ctx.user.has_perms(f.obj, f.obj.PERM_READ):
                if mimetype.startswith('image'):
                    description = '<img src="%s" />' % unicode(link.setvars(view='thumbnail', thumb_size=200))
                elif mimetype.startswith('text'):
                    with open(f.obj.get_realpath(), 'r') as fp:
                        description = fp.read()
                        if not 'html' in mimetype:
                            description = '<pre>%s</pre>' % html_escape(description.decode('utf-8'))
            title = f.obj.path[len(self.ctx.file.path):].replace('_', ' ').lstrip('/').replace('/', ' / ')
            if title.endswith('.html') or title.endswith('.txt'):
                title = title.rsplit('.', 1)[0]
            items.append(PyRSS2Gen.RSSItem(title=title,
                                           link=str(link),
                                           description=description,
                                           guid=PyRSS2Gen.Guid(f.obj.path),
                                           pubDate=f.mtime))
        rss = PyRSS2Gen.RSS2(title='Updates of %s/' % self.ctx.file.path,
                             link='%s' % build_url(root_url, self.ctx.file, user=self.ctx.user),
                             description='Last updates of %s/' % self.ctx.file.path,
                             lastBuildDate=files[0].mtime if len(files) else base_dir.mtime,
                             items=items)
        self.ctx.res.content_type = 'application/rss+xml'
        self.ctx.res.charset = 'UTF-8'
        self.ctx.res.body = rss.to_xml('utf-8')

class ApiPlugin(Plugin):
    def init(self):
        self.register_web_view(
            View(object_type=None, name='json_info', public=False, verbose_name='JSON info'),
            JsonInfoAction, -1)

        self.register_web_view(
            View(object_type='directory', name='json_list', public=False, verbose_name='JSON list'),
            JsonListAction, -1)

        self.register_web_view(
            View(object_type='directory', name='text_list', public=False, verbose_name='Text-only list'),
            TextListAction, -1)

        self.register_web_view(
            View(object_type='directory', name='rss', public=True, verbose_name='RSS feed'),
            RssListAction, -1)
