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
import posixpath
import hashlib
import mimetypes
from math import log
from datetime import datetime

from .obj import IObject

__all__ = ['File']


class File(IObject):
    PERM_READ =  0x001
    PERM_LIST =  0x002
    PERM_WRITE = 0x004

    PERM_ALL =   0xfff

    PERMS = (('r', PERM_READ),
             ('l', PERM_LIST),
             ('w', PERM_WRITE)
            )

    @staticmethod
    def p2str(perms):
        s = ''
        for letter, perm in File.PERMS:
            s += letter if (perms & perm) else '-'
        return s

    @staticmethod
    def str2p(s):
        perms = 0
        for letter in s:
            perms |= dict(File.PERMS)[letter]
        return perms

    def __init__(self, storage, path):
        # skip any trailing /
        if len(path) > 0 and path[-1] == '/':
            path = path[:-1]

        self.path = path
        self.view = None
        self.perms = {}
        IObject.__init__(self, storage)

    def __str__(self):
        return self.path

    def set_all_perms(self, perms):
        self.perms['all'] = perms

    def set_auth_perms(self, perms):
        self.perms['auth'] = perms

    def set_group_perms(self, name, perms):
        self.perms['g.%s' % name] = perms

    def set_user_perms(self, name, perms):
        self.perms['u.%s' % name] = perms

    def get_all_perms(self, default=None):
        return self.perms.get('all', default)

    def get_auth_perms(self, default=None):
        return self.perms.get('auth', default)

    def get_group_perms(self, name, default=None):
        return self.perms.get('g.%s' % name, default)

    def get_user_perms(self, name, default=None):
        return self.perms.get('u.%s' % name, default)

    def clear_all_perms(self):
        self.perms.pop('all', None)

    def clear_auth_perms(self):
        self.perms.pop('auth', None)

    def clear_group_perms(self):
        for name in self.perms.keys():
            if name.startswith('g.'):
                self.perms.pop(name)

    def clear_user_perms(self):
        for name in self.perms.keys():
            if name.startswith('u.'):
                self.perms.pop(name)

    def parent(self):
        if self.path == '':
            return None
        return self.storage.get_file(posixpath.dirname(self.path))

    def get_realpath(self):
        return os.path.realpath(os.path.join(self.storage.path, '..', self.path[1:]))

    def get_size(self):
        return os.path.getsize(self.get_realpath())

    def get_mtime(self):
        return datetime.fromtimestamp(os.path.getmtime(self.get_realpath()))

    def get_human_size(self):
        size = self.get_size()
        if size:
            units = ('B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB')
            exponent = int(log(size, 1024))
            return "%.1f %s" % (float(size) / pow(1024, exponent), units[exponent])
        return '0 B'

    def file_exists(self):
        """
        Tests if the real file exists (not the File storage object)
        """
        return os.path.exists(self.get_realpath())

    def isdir(self):
        return os.path.isdir(self.get_realpath())

    def isfile(self):
        return os.path.isfile(self.get_realpath())

    def get_object_type(self):
        if self.isdir():
            return "directory"
        elif self.isfile():
            return "file"

    def iter_children(self):
        if self.isdir():
            filenames = sorted(os.listdir(self.get_realpath()))
            for filename in filenames:
                yield self.storage.get_file(posixpath.join("/", self.path, filename))

    def get_name(self):
        return posixpath.basename(self.path)

    def get_mimetype(self):
        return mimetypes.guess_type(self.get_name())[0]

    def get_hash(self):
        return hashlib.sha1(self.path).hexdigest()

    def _get_confname(self):
        return os.path.join('files', self.get_hash())

    def _postread(self):
        self.view = self.data['info'].get('view', None)
        if self.view in ["", "None"]:
            self.view = None
        self.perms.clear()
        for key, value in self.data.get('perms', {}).iteritems():
            self.perms[key] = int(value)

    def _prewrite(self):
        if self.view is not None:
            self.data['info']['view'] = self.view
        else:
            self.data['info'].pop('view', None)
        self.data['info']['path'] = self.path
        self.data['perms'] = self.perms


class UnknownFile(File):
    """
    File not know by its path, but only by its hash.
    This should only be used for special cases.
    """

    def __init__(self, storage, hsh):
        self._confname = os.path.join('files', hsh)
        File.__init__(self, storage, '')
        self.read()
        self.path = self.data['info'].get('path')

    def _get_confname(self):
        return self._confname
