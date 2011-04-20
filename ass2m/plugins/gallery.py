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
from PIL import Image
from paste.httpheaders import CACHE_CONTROL

from ass2m.plugin import Plugin
from ass2m.routes import View
from ass2m.server import ViewAction, FileApp

class ListGalleryAction(ViewAction):
    def get(self):
        dirs = []
        photos = []
        description = None
        for f in self.ctx.iter_files():
            if f.isdir():
                dirs.append(f)
            elif self.ctx.user.has_perms(f, f.PERM_READ):
                filename = f.get_name()
                mimetype = f.get_mimetype()
                if mimetype is not None and mimetype.startswith('image'):
                    photos.append(f)
                elif filename == 'DESCRIPTION':
                    with open(f.get_realpath(), 'r') as f:
                        description = f.read()

        self.ctx.template_vars['dirs'] = dirs
        self.ctx.template_vars['photos'] = photos
        self.ctx.template_vars['description'] = description
        self.ctx.res.body = self.ctx.render('list-gallery.html')

class DownloadThumbnailAction(ViewAction):
    DEFAULT_SIZE = 300

    def _get_size(self):
        try:
            size = int(self.ctx.req.str_GET['thumb_size'])
        except (KeyError,ValueError):
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

        mtime = os.path.getmtime(f.get_realpath())
        if not os.path.exists(thumbpath) or mtime > os.path.getmtime(thumbpath):
            if not os.path.isdir(os.path.dirname(thumbpath)):
                os.makedirs(os.path.dirname(thumbpath))
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
        self.ctx.res.cache_control(public=True, max_age=CACHE_CONTROL.ONE_HOUR)


class GalleryPlugin(Plugin):
    def init(self):
        self.register_web_view(
            View(object_type='directory', name='gallery'),
            ListGalleryAction)
        self.register_web_view(
            View(object_type='file', mimetype='image', name='thumbnail'),
            DownloadThumbnailAction)
