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


class IUser(object):
    name = None
    email = None
    realname = None
    groups = []

    def has_perms(self, f):
        raise NotImplementedError()

class User(object):
    def __init__(self, storage, name):
        self.storage = storage
        self.name = name
        self.email = None
        self.realname = None
        self.groups = []

    def save(self):
        self.storage.save_user(self)

class Anonymous(IUser):
    name = '<anonymous>'
    email = None
    realname = 'Ano Nymous'
    groups = []
