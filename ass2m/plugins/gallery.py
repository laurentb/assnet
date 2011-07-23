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
from paste.httpheaders import CACHE_CONTROL, CONTENT_DISPOSITION
from mako.filters import html_escape

from ass2m.plugin import Plugin
from ass2m.routes import View
from ass2m.server import ViewAction, FileApp


__all__ = ['GalleryPlugin']


class DownloadThumbnailAction(ViewAction):
    DEFAULT_SIZE = 300

    def _get_size(self):
        try:
            size = int(self.ctx.req.str_GET['thumb_size'])
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


class GalleryPlugin(Plugin):
    def init(self):
        self.register_web_view(
            View(object_type='file', mimetype='image', name='thumbnail'),
            DownloadThumbnailAction, -1)
