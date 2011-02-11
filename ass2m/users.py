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

    def has_perms(self, f, perm):
        raise NotImplementedError()

class User(IUser):
    def __init__(self, storage, name):
        self.storage = storage
        self.name = name
        self.email = None
        self.realname = None
        self.password = None
        self.groups = []

    def save(self):
        self.storage.save_user(self)

    def has_perms(self, f, perm):
        f_perms = f.get_user_perms(self.name)
        if f_perms is not None and f_perms & perm:
            return True

        for group in self.groups:
            f_perms = f.get_group_perms(group)
            if f_perms is not None and f.get_group_perms(group) & perm:
                return True

        f_perms = f.get_all_perms()
        if f_perms is not None:
            return f_perms & perm

        f_parent = f.parent()
        return f_parent and self.has_perms(f_parent, perm)

class Anonymous(IUser):
    name = '<anonymous>'
    email = None
    realname = 'Ano Nymous'
    groups = []

    def has_perms(self, f, perm):
        f_perms = f.get_all_perms()
        if f_perms is not None:
            return f_perms & perm

        f_parent = f.parent()
        return f_parent and self.has_perms(f_parent, perm)
