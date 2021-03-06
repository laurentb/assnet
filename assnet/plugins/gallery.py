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


import os
from PIL import Image
from paste.httpheaders import CACHE_CONTROL, CONTENT_DISPOSITION
from mako.filters import html_escape
from paste.url import URL

from assnet.plugin import Plugin
from assnet.routes import View
from assnet.server import ViewAction, FileApp
from assnet.files import File


__all__ = ['GalleryPlugin']


class DownloadThumbnailAction(ViewAction):
    DEFAULT_SIZE = 300

    def _get_size(self):
        try:
            size = int(self.ctx.req.GET['thumb_size'])
        except (KeyError, ValueError):
            size = self.DEFAULT_SIZE
        else:
            if size < 1 or size > 1000:
                size = self.DEFAULT_SIZE
        return size

    def get(self):
        size = self._get_size()
        thumbdir = os.path.join(self.ctx.storage.path, 'thumbnails')
        f = self.ctx.file

        # use a lossless format in doubt
        lossy = f.get_mimetype() == 'image/jpeg'
        thumbext = 'jpg' if lossy else 'png'
        thumbpath = os.path.join(thumbdir, str(size), '%s.%s' % (f.get_hash(), thumbext))
        f.data['thumbnail']['ext'] = thumbext
        f.save()

        mtime = int(os.path.getmtime(f.get_realpath()))
        if not os.path.exists(thumbpath) or mtime != int(os.path.getmtime(thumbpath)):
            if not os.path.isdir(os.path.dirname(thumbpath)):
                os.makedirs(os.path.dirname(thumbpath))
                os.chmod(os.path.dirname(thumbpath), 0770)
            with open(f.get_realpath(), 'rb') as fp:
                img = Image.open(fp)
                img.thumbnail((size, size), Image.BILINEAR)
                with open(thumbpath, 'wb') as tfp:
                    if lossy:
                        img.save(tfp, 'jpeg', quality=95)
                    else:
                        img.save(tfp, 'png')
            os.utime(thumbpath, (mtime, mtime))

        self.ctx.res = FileApp(thumbpath)
        self.ctx.res.cache_control(private=True, max_age=CACHE_CONTROL.ONE_HOUR)
        CONTENT_DISPOSITION.apply(self.ctx.res.headers, inline=True,
            filename="%s_thumb_%s.%s" % (os.path.splitext(f.get_name())[0], size, thumbext))


class Media(File):
    def get_url(self):
        return URL(self.get_name())

    def get_thumb_url(self):
        if self.is_vector():
            return self.get_url()
        return self.get_url().setvars(view='thumbnail', thumb_size=200)

    def is_vector(self):
        return self.get_mimetype() == 'image/svg+xml'

    def get_extra_classes(self):
        if self.is_vector():
            return ' vector'
        return ''


class MediaListAction(ViewAction):
    IS_MEDIA = True

    def get(self):
        dirs = []
        files = []
        thumbs = []
        self.ctx.template_vars['header_text'] = None
        self.ctx.template_vars['readme_text'] = None
        for f in self.ctx.iter_files():
            if f.isdir():
                dirs.append(f)
                continue
            if self.ctx.user.has_perms(f, f.PERM_READ):
                filename = f.get_name()
                mimetype = f.get_mimetype()
                if self.IS_MEDIA and mimetype is not None and mimetype.startswith('image'):
                    m = f.to_class(Media)
                    thumbs.append(m)
                    continue
                if filename in ('README', 'README.html', 'HEADER', 'HEADER.html'):
                    with open(f.get_realpath(), 'r') as fp:
                        text = fp.read()
                        if not filename.endswith('.html'):
                            text = '<pre>%s</pre>' % html_escape(text.decode('utf-8'))
                        self.ctx.template_vars['%s_text' % os.path.splitext(filename)[0].lower()] = text
                    continue
            files.append(f)

        self.ctx.template_vars['thumbs'] = thumbs
        self.ctx.template_vars['dirs'] = dirs
        self.ctx.template_vars['files'] = files
        self.ctx.template_vars['scripts'].append('list.js')
        self.ctx.res.body = self.ctx.render('list.html')


class GalleryPlugin(Plugin):
    def init(self):
        self.register_web_view(
            View(object_type='file', mimetype='image', name='thumbnail'),
            DownloadThumbnailAction, -1)
        self.register_web_view(
                View(object_type='directory', name='medialist', verbose_name='Media list'),
                MediaListAction, 2)
