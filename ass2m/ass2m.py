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
from storage import Storage

class NotWorkingDir(Exception): pass

class Ass2m(object):
    DIRNAME = '.ass2m'

    def __init__(self, path):
        if isinstance(path, Storage):
            storage = path
        elif not path:
            raise NotWorkingDir()
        else:
            try:
                while not self.DIRNAME in os.listdir(path) and path != os.path.dirname(path):
                    path = os.path.dirname(path)
            except OSError:
                raise NotWorkingDir()
            if path == os.path.dirname(path):
                raise NotWorkingDir()

            storage = Storage(os.path.join(path, self.DIRNAME))
        self.storage = storage
        self.root = os.path.realpath(os.path.join(storage.path, os.path.pardir))

    @classmethod
    def create(cls, path):
        return cls(Storage.init(os.path.join(path, cls.DIRNAME)))
