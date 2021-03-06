# -*- coding: utf-8 -*-

# Copyright (C) 2011 Romain Bignon, Laurent Bachelier
#
# This file is part of assnet.
#
# assnet is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# assnet is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with assnet. If not, see <http://www.gnu.org/licenses/>.


__all__ = ['Group', 'IUser', 'User', 'Anonymous']


from .obj import IObject
from .mail import Mail
from .security import new_salt, new_user_key

import os
import hashlib


class Group(object):
    def __init__(self, name):
        self.name = name
        self.description = u''
        self.users = []

    def __str__(self):
        return self.name

    def __lt__(self, g):
        return self.name < g.name


class IUser(object):
    def has_perms(self, f, perm):
        raise NotImplementedError()

    def __str__(self):
        return self.name


class User(IUser, IObject):
    def __init__(self, storage, name):
        self.name = name
        self.email = None
        self.realname = None
        self.password = None
        self.key = None
        self.groups = []
        IObject.__init__(self, storage)

    def has_perms(self, f, perm):
        f_perms = f.get_user_perms(self.name)
        if f_perms is not None:
            return f_perms & perm

        for group in self.groups:
            f_perms = f.get_group_perms(group)
            if f_perms is not None:
                return f.get_group_perms(group) & perm

        f_perms = f.get_auth_perms()
        if f_perms is not None:
            return f_perms & perm

        f_perms = f.get_all_perms()
        if f_perms is not None:
            return f_perms & perm

        f_parent = f.parent()
        return f_parent and self.has_perms(f_parent, perm)

    def new_mail(self, template, subject):
        config = self.storage.get_config()
        sender = config.data['mail'].get('sender', 'assnet')
        recipient = '%s <%s>' % (self.realname, self.email)
        smtp = config.data['mail'].get('smtp', 'localhost')

        mail = Mail(self.storage, template, sender, recipient, subject, smtp)
        return mail

    def gen_key(self):
        self.key = new_user_key()

    def _get_confname(self):
        return os.path.join('users', self.name)

    def _postread(self):
        self.email = self.data['info'].get('email')
        self.realname = self.data['info'].get('realname')
        self.password = len(self.data['auth'].get('password', '') \
                            + self.data['auth'].get('salt', '')) > 0
        self.key = self.data['auth'].get('key')
        for group in self.storage.get_groupscfg().itervalues():
            if self.name in group.users:
                self.groups.append(group.name)

    def _prewrite(self):
        self.data['info']['email'] = self.email if self.email else None
        self.data['info']['realname'] = self.realname if self.realname else None
        self.data['auth']['key'] = self.key if self.key else None
        # only update password when set
        if isinstance(self.password, basestring):
            salt = new_salt()
            version = 1
            hpwd = self.hash_password(self.password, salt, version)
            self.data['auth']['password'] = hpwd
            self.data['auth']['salt'] = salt
            self.data['auth']['version'] = version
            self.password = True

    @staticmethod
    def hash_password(password, salt, version):
        assert version == 1  # the only one supported for now
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
    realname = 'Anonymous'
    password = None
    groups = []
    exists = False
    key = None
    groups = []

    def __init__(self, fake_name=None):
        if fake_name:
            self.name = fake_name

    def has_perms(self, f, perm):
        f_perms = f.get_all_perms()
        if f_perms is not None:
            return f_perms & perm

        f_parent = f.parent()
        return f_parent and self.has_perms(f_parent, perm)

    def is_valid_password(self, password):
        return False
