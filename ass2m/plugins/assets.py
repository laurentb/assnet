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


from contextlib import closing
import os
import re
from gzip import GzipFile
from mimetypes import guess_type

from ass2m.plugin import Plugin
from ass2m.server import Action, FileApp

from paste.httpheaders import CACHE_CONTROL, CONTENT_DISPOSITION
from webob.exc import HTTPNotFound, HTTPPreconditionFailed


__all__ = ['AssetsPlugin']


class AssetAction(Action):
    SANITIZE_REGEXP = re.compile(r'^[\w\-]+(?:\.[\w\-]+)+$')

    def get(self):
        filename = self.ctx.req.str_GET.get('file')
        if self.SANITIZE_REGEXP.match(filename):
            realpath = self.find_file(filename)
            if realpath:
                if self.accepts_gzip() and self.compressible(filename):
                    realpath = self.gzip_file(realpath)
                self.ctx.res = FileApp(realpath)
                self.ctx.res.cache_control(public=True, max_age=CACHE_CONTROL.ONE_DAY)
                CONTENT_DISPOSITION.apply(self.ctx.res.headers, inline=True, filename=filename)
                return
            raise HTTPNotFound()
        raise HTTPPreconditionFailed()

    def find_file(self, filename):
            paths = [os.path.join(path, 'assets') for path in self.ctx.storage.DATA_PATHS]
            for path in paths:
                realpath = os.path.join(path, filename)
                if os.path.isfile(realpath):
                    return realpath

    def accepts_gzip(self):
        return 'gzip' in self.ctx.req.accept_encoding

    def compressible(self, filename):
        mimetype = guess_type(filename)[0]
        return mimetype.startswith('application/') or mimetype.startswith('text/')

    def gzip_file(self, realpath):
        filename = os.path.basename(realpath)
        mtime = int(os.path.getmtime(realpath))

        # first look if there is a (read-only) gzipped version of the asset
        # these files may be created by installers and are supposed to be
        # always up to date
        realpath_gz = realpath + '.gz'
        if os.path.exists(realpath_gz):
            return realpath_gz

        # then look for a local cache of that asset, if not present, create it
        cachedir = os.path.join(self.ctx.storage.path, 'assets_cache')
        dest = os.path.join(cachedir, filename + '.gz')
        if not os.path.exists(dest) or mtime != int(os.path.getmtime(dest)):
            if not os.path.isdir(cachedir):
                try:
                    os.makedirs(cachedir)
                    os.chmod(cachedir, 0770)
                except OSError, e:
                    # ignore race condition when multiple assets
                    # are asked at the same
                    if not e.errno == 17:
                        raise e
            with open(realpath, 'rb') as f_in:
                with closing(GzipFile(dest, 'wb')) as f_out:
                    f_out.writelines(f_in)
            os.utime(dest, (mtime, mtime))
        return dest


class AssetsPlugin(Plugin):
    def init(self):
        self.register_web_action('asset', AssetAction)
