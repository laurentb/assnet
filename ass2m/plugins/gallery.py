# -*- coding: utf-8 -*-

# Copyright(C) 2011  Romain Bignon, Laurent Bachelier
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import os
import posixpath
import Image
import mimetypes
from cStringIO import StringIO
from paste.fileapp import DataApp

from ass2m.plugin import Plugin
from ass2m.routes import Route
from ass2m.server import Action

class ListGalleryAction(Action):
    def answer(self):
        dirs = []
        photos = []
        description = None
        for filename in sorted(os.listdir(self.ctx.realpath)):
            f = self.ctx.ass2m.storage.get_file(posixpath.join(self.ctx.webpath, filename))
            if not self.ctx.user.has_perms(f, f.PERM_LIST):
                continue

            if os.path.isdir(f.get_disk_path()):
                dirs.append(filename.decode('utf-8'))
                continue

            if not self.ctx.user.has_perms(f, f.PERM_READ):
                continue

            mimetype = mimetypes.guess_type(f.get_disk_path())[0]
            if mimetype is not None and mimetype.startswith('image'):
                photos.append(filename.decode('utf-8'))
            elif filename == 'DESCRIPTION':
                with open(f.get_disk_path(), 'r') as f:
                    description = f.read()

        self.ctx.template_vars['dirs'] = dirs
        self.ctx.template_vars['photos'] = photos
        self.ctx.template_vars['description'] = description
        self.ctx.res.body = self.ctx.render('list-gallery.html')

class DownloadThumbnailAction(Action):
    DEFAULT_SIZE = 300

    def answer(self):
        img = Image.open(self.ctx.realpath)

        try:
            size = int(self.ctx.req.str_GET['thumb_size'])
        except (KeyError,ValueError):
            size = self.DEFAULT_SIZE
        else:
            if size < 1 or size > 1000:
                size = self.DEFAULT_SIZE

        img.thumbnail((size,size))
        s = StringIO()
        img.save(s, 'jpeg')
        self.ctx.res = DataApp(None, content_type='image/jpeg')
        self.ctx.res.set_content(s.getvalue(), os.path.getmtime(self.ctx.realpath))

class GalleryPlugin(Plugin):
    def init(self):
        self.register_web_action(
            Route(object_type = "directory", action="list", view="gallery"),
            ListGalleryAction)
        self.register_web_action(
            Route(object_type = "file", action="download", view="thumbnail"),
            DownloadThumbnailAction)
