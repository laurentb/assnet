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


from __future__ import with_statement

import os
from ConfigParser import RawConfigParser
from .users import User, Anonymous
from .files import File
from .obj import IObject, ConfigDict


__all__ = ['Storage']


class GlobalConfig(IObject):
    def _get_confname(self):
        return 'config'


class Storage(object):
    def __init__(self, path):
        self.path = path

    @classmethod
    def init(cls, path):
        storage = cls(path)

        # Default perms on /.ass2m
        f = File(storage, '/.ass2m')
        f.perms = {'all': 0}
        f.save()

        # Default perms on /
        f = File(storage, '')
        f.perms = {'all': File.PERM_READ|File.PERM_LIST}
        f.save()

        return storage

    def get_user(self, name):
        user = User(self, name)
        user.read()
        if not user.exists:
            return Anonymous()
        return user

    def iter_users(self):
        usersdir = os.path.join(self.path, 'users')
        if os.path.exists(usersdir):
            for name in sorted(os.listdir(usersdir)):
                user = self.get_user(name)
                if user:
                    yield user

    def user_exists(self, name):
        user = User(self, name)
        user.read()
        return user.exists

    def get_disk_file(self, diskpath):
        path = os.path.relpath(diskpath, os.path.realpath(os.path.join(self.path, os.path.pardir)))
        if path.startswith('../'):
            # Outside of working tree.
            return None
        if path == '.':
            # Root
            path = '/'
        else:
            path = '/' + path

        return self.get_file(path)

    def get_file(self, path):
        f = File(self, path)
        f.read()
        return f

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
            data[sec] = dict([(k,v.decode('utf-8')) for k,v in config.items(sec)])

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
                config.set(sec, key, value)
        with open(path, 'wb') as fp:
            config.write(fp)

    def _get_mtime(self, name):
        path = os.path.join(self.path, name)
        if os.path.exists(path):
            return os.path.getmtime(path)

    def _remove(self, name):
        path = os.path.join(self.path, name)
        os.unlink(path)
