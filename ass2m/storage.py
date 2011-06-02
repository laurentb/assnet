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
import sys
from ConfigParser import RawConfigParser

from .users import Group, User, Anonymous
from .files import File, UnknownFile
from .obj import IObject, ConfigDict


__all__ = ['Storage']


class GlobalConfig(IObject):
    def __str__(self):
        return '<global>'

    def _get_confname(self):
        return 'config'


class GroupsConfig(IObject, dict):
    def __init__(self, storage):
        IObject.__init__(self, storage)
        dict.__init__(self)

    def _get_confname(self):
        return 'groups'

    def _postread(self):
        for name, values in self.data.iteritems():
            group = Group(name)
            if 'users' in values:
                group.users = values['users'].split()
            group.description = values.get('description', '')
            self[name] = group

    def _prewrite(self):
        self.data = ConfigDict()
        for name, group in self.iteritems():
            self.data[name] = {}
            self.data[name]['users'] = ' '.join([uname for uname in group.users])
            self.data[name]['description'] = group.description


class Storage(object):
    DIRNAME = '.ass2m'
    DATA_PATHS = [os.path.realpath(os.path.join(os.path.dirname(__file__), os.path.pardir, 'data')),
        os.path.join(sys.prefix, 'share', 'ass2m'),
        os.path.join(sys.prefix, 'local', 'share', 'ass2m')]

    def __init__(self, path):
        self.path = path
        self.DATA_PATHS.insert(0, os.path.realpath(os.path.join(self.path, 'data')))

    @property
    def root(self):
        return os.path.realpath(os.path.join(self.path, os.path.pardir))

    @classmethod
    def lookup(cls, path):
        if not path:
            return None

        try:
            while not os.path.isdir(os.path.join(path, cls.DIRNAME)) and path != os.path.dirname(path):
                path = os.path.dirname(path)
        except OSError:
            path = None

        if path and path != os.path.dirname(path):
            return cls(os.path.join(path, cls.DIRNAME))
        else:
            return None

    @classmethod
    def create(cls, path):
        storage = cls(os.path.join(path, cls.DIRNAME))

        # Default perms on /.ass2m
        f = File(storage, '/.ass2m')
        f.perms = {'all': 0}
        f.save()

        # Default perms on /
        f = File(storage, '')
        f.perms = {'all': File.PERM_READ | File.PERM_LIST}
        f.save()

        return storage

    def get_user(self, name, want_fake=True):
        """
        Get a particular user by its name.
        Returns Anonymous if no user is found.
        """
        user = User(self, name)
        user.read()
        if not user.exists:
            if want_fake:
                return Anonymous(name)
            return Anonymous()
        return user

    def iter_users(self):
        """
        Get all stored users.
        """
        usersdir = os.path.join(self.path, 'users')
        if os.path.exists(usersdir):
            for name in sorted(os.listdir(usersdir)):
                user = self.get_user(name)
                yield user

    def iter_files(self):
        """
        Get all files with a stored configuration.
        """
        filesdir = os.path.join(self.path, 'files')
        if os.path.exists(filesdir):
            for hsh in sorted(os.listdir(filesdir)):
                f = UnknownFile(self, hsh)
                yield f

    def user_exists(self, name):
        """
        Test if an user exists by its name. Returns boolean.
        """
        user = User(self, name)
        user.read()
        return user.exists

    def get_file_from_realpath(self, realpath):
        path = os.path.relpath(realpath, os.path.realpath(os.path.join(self.path, os.path.pardir)))
        if path.startswith('../'):
            # Outside of working tree.
            return None
        if path == '.':
            # Root
            path = ''
        else:
            path = '/' + path

        return self.get_file(path)

    def get_file(self, path):
        f = File(self, path)
        f.read()
        return f

    def get_groupscfg(self):
        groups = GroupsConfig(self)
        groups.read()
        return groups

    def get_config(self):
        cfg = GlobalConfig(self)
        cfg.read()
        return cfg

    def _read(self, name):
        path = os.path.join(self.path, name)
        config = RawConfigParser()
        try:
            with open(path, 'r') as fp:
                config.readfp(fp)
        except IOError:
            return None

        data = ConfigDict()
        for sec in config.sections():
            data[sec] = dict([(k, v.decode('utf-8')) for k, v in config.items(sec)])

        return data

    def _write(self, name, data):
        path = os.path.join(self.path, name)
        destdir = os.path.dirname(path)
        if not os.path.exists(destdir):
            os.makedirs(destdir)
        config = RawConfigParser()
        for sec, items in data.iteritems():
            config.add_section(sec)
            for key, value in items.iteritems():
                if isinstance(value, unicode):
                    value = value.encode('utf-8')
                if value is not None:
                    config.set(sec, key, value)
        with open(path, 'wb') as fp:
            config.write(fp)

    def _get_mtime(self, name):
        path = os.path.join(self.path, name)
        if os.path.exists(path):
            return int(os.path.getmtime(path))

    def _remove(self, name):
        path = os.path.join(self.path, name)
        os.unlink(path)
