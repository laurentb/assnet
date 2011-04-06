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


from collections import defaultdict
from copy import deepcopy

class IObject(object):
    def __init__(self, storage):
        self._storage = storage
        self._confname = self._get_confname()
        self._mtime = None
        self._old_data = None
        self.exists = None
        self.data = ConfigDict()

    def _get_confname(self):
        raise NotImplementedError()

    def _postread(self):
        pass

    def _prewrite(self):
        pass

    def read(self):
        mtime = self._storage._get_mtime(self._confname)
        if self._mtime is None or self._mtime < mtime or self._old_data != self.data:
            data = self._storage._read(self._confname)
            self._mtime = mtime
            self.exists = data is not None
            self.data = data or ConfigDict()
            self._postread()
            self._old_data = deepcopy(self.data)

    def save(self):
        self._prewrite()
        self.data.cleanup()
        # only write as needed
        if self._old_data is None or self._old_data != self.data or self.exists is not True:
            self._storage._write(self._confname, self.data)
            self._old_data = deepcopy(self.data)
            self._mtime = self._storage._get_mtime(self._confname)
            self.exists = True

    def remove(self):
        self._storage._remove(self._confname)
        self._mtime = None
        self.exists = False
        self.data.clear()
        self._postread()

class ConfigDict(defaultdict):
    def __init__(self, _ = None):
        defaultdict.__init__(self, dict)

    def cleanup(self):
        for key in self.keys():
            if not len(self[key]):
                del self[key]
