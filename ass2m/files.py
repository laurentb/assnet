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

import os
import hashlib
from .obj import IObject

__all__ = ['File']


class File(IObject):
    PERM_READ =  0x001
    PERM_LIST =  0x002
    PERM_WRITE = 0x004

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

        self.storage = storage
        self.path = path
        self.view = None
        self.perms = {}
        IObject.__init__(self, storage)

    def set_all_perms(self, perms):
        self.perms['all'] = perms

    def set_group_perms(self, name, perms):
        self.perms['g.%s' % name] = perms

    def set_user_perms(self, name, perms):
        self.perms['u.%s' % name] = perms

    def get_all_perms(self, default=None):
        return self.perms.get('all', default)

    def get_group_perms(self, name, default=None):
        return self.perms.get('g.%s' % name, default)

    def get_user_perms(self, name, default=None):
        return self.perms.get('u.%s' % name, default)

    def parent(self):
        if self.path == '':
            return None
        return self.storage.get_file(os.path.dirname(self.path))

    def get_realpath(self):
        return os.path.realpath(os.path.join(self.storage.path, '..', self.path[1:]))

    def _get_confname(self):
        return os.path.join('files', hashlib.sha1(self.path).hexdigest())

    def _postread(self):
        self.view = self.data['info'].get('view', None)
        self.perms.clear()
        for key, value in self.data.get('perms', {}).iteritems():
            self.perms[key] = int(value)

    def _prewrite(self):
        if self.view is not None:
            self.data['info']['view'] = self.view
        self.data['info']['path'] = self.path
        self.data['perms'] = self.perms
