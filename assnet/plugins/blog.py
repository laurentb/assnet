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


from mako.filters import html_escape

from assnet.plugin import Plugin

from assnet.routes import View
from assnet.server import ViewAction


__all__ = ['BlogPlugin']


class Post(object):
    def __init__(self):
        self.path = u''
        self.date = None
        self.title = None
        self.content = None


class BlogAction(ViewAction):
    def get(self):
        f = self.ctx.file
        post = Post()
        post.path = f.get_name()
        post.date = f.get_mtime()
        post.title = f.get_name().replace('_', ' ') \
                                  .lstrip('/') \
                                  .replace('/', ' / ') \
                                  .rsplit('.', 1)[0]

        with open(f.get_realpath(), 'r') as fp:
            post.content = fp.read()
            if not 'html' in f.get_mimetype():
                post.content = '<pre>%s</pre>' % html_escape(post.content.decode('utf-8'))

        self.ctx.template_vars['categories'] = []
        self.ctx.template_vars['posts'] = [post]
        self.ctx.template_vars['stylesheets'].append('blog.css')
        self.ctx.res.body = self.ctx.render('blog.html')


class BlogListAction(ViewAction):
    NB_ENTRIES = 20

    class SortableFile(object):
        def __init__(self, f):
            self.obj = f
            self.mtime = f.get_mtime()

        def __lt__(self, o):
            return self.mtime < o.mtime

    def get(self):
        posts = []
        categories = []
        files = []
        for f in self.ctx.iter_files_recursively():
            if f.path != self.ctx.file.path:
                files.append(self.SortableFile(f))
        files.sort(reverse=True)

        for f in files[:self.NB_ENTRIES]:
            if f.obj.isdir():
                categories.append(f.obj)
                continue
            if not self.ctx.user.has_perms(f.obj, f.obj.PERM_READ):
                continue

            mimetype = f.obj.get_mimetype()
            if mimetype is None or not mimetype.startswith('text'):
                continue

            post = Post()
            post.path = f.obj.path[len(self.ctx.file.path):].lstrip('/')
            post.date = f.mtime
            post.title = f.obj.path[len(self.ctx.file.path):].replace('_', ' ') \
                                                              .lstrip('/') \
                                                              .replace('/', ' / ') \
                                                              .rsplit('.', 1)[0]

            with open(f.obj.get_realpath(), 'r') as fp:
                post.content = fp.read()
                if not 'html' in mimetype:
                    post.content = '<pre>%s</pre>' % html_escape(post.content.decode('utf-8'))

            posts.append(post)

        self.ctx.template_vars['categories'] = categories
        self.ctx.template_vars['posts'] = posts
        self.ctx.template_vars['stylesheets'].append('blog.css')
        self.ctx.res.body = self.ctx.render('blog.html')


class BlogPlugin(Plugin):
    def init(self):
        self.register_web_view(
            View(object_type='directory', name='blog', public=False, verbose_name='Blog'),
            BlogListAction, -1)
        self.register_web_view(
            View(object_type='file', name='blog', public=False, verbose_name='Blog'),
            BlogAction, -1)
