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


__all__ = ['Group', 'IUser', 'User', 'Anonymous']


from .obj import IObject
import os
import hashlib
from binascii import hexlify

class Group(object):
    def __init__(self, name):
        self.name = name
        self.users = []

class IUser(object):
    name = None
    email = None
    realname = None
    groups = []

    def has_perms(self, f, perm):
        raise NotImplementedError()

    def __str__(self):
        return self.name

class User(IUser, IObject):
    def __init__(self, storage, name):
        self.storage = storage
        self.name = name
        self.email = None
        self.realname = None
        self.password = None
        self.groups = []
        IObject.__init__(self, storage)

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

    def _get_confname(self):
        return os.path.join('users', self.name)

    def _postread(self):
        self.email = self.data['info'].get('email')
        self.realname = self.data['info'].get('realname')
        self.password = len(self.data['auth'].get('password', '') \
                            + self.data['auth'].get('salt', '')) > 0

    def _prewrite(self):
        self.data['info']['email'] = self.email if self.email else None
        self.data['info']['realname'] = self.realname if self.realname else None
        # only update password when set
        if isinstance(self.password, basestring):
            salt = hexlify(os.urandom(42))
            version = 1
            hpwd = self.hash_password(self.password, salt, version)
            self.data['auth']['password'] = hpwd
            self.data['auth']['salt'] = salt
            self.data['auth']['version'] = version
            self.password = True

    @staticmethod
    def hash_password(password, salt, version):
        assert version == 1 # the only one supported for now
        return hashlib.sha512(password + salt).hexdigest()

    def is_valid_password(self, password):
        assert isinstance(password, basestring)
        if isinstance(self.password, basestring):
            return self.password == password
        if self.password is True:
            hpwd = self.hash_password(password, \
                    self.data['auth']['salt'], \
                    int(self.data['auth']['version']))
            return hpwd == self.data['auth']['password']


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

    def is_valid_password(self, password):
        return False
