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
import hashlib
from ConfigParser import RawConfigParser
from users import User, Anonymous
from files import File

class Group(object):
    def __init__(self, name):
        self.name = name
        self.users = []

class Storage(object):
    def __init__(self, path):
        self.path = path

    @classmethod
    def init(cls, path):
        os.mkdir(path)
        os.mkdir(os.path.join(path, 'users'))
        os.mkdir(os.path.join(path, 'files'))
        storage = cls(path)

        # Default perms on /.ass2m
        f = File(storage, '/.ass2m')
        f.perms = {'all': 0}
        f.save()

        # Default perms on /
        f = File(storage, '')
        f.perms = {'all': f.PERM_READ|f.PERM_LIST}
        f.save()
        return storage

    def get_user(self, name):
        config = self._get_config(os.path.join(self.path, 'users', name))
        if not config:
            return Anonymous()

        user = User(self, name)
        info = dict([(k,v.decode('utf-8')) for k,v in config.items('info')])
        user.email = info.get('email', None)
        user.realname = info.get('realname', None)
        user.password = info.get('password', None)
        return user

    def iter_users(self):
        for name in sorted(os.listdir(os.path.join(self.path, 'users'))):
            user = self.get_user(name)
            if user:
                yield user

    def user_exists(self, name):
        return name in os.listdir(os.path.join(self.path, 'users'))

    def save_user(self, user):
        sections = {}
        sections['info'] = {'email':    user.email.encode('utf-8') if user.email else None,
                            'realname': user.realname.encode('utf-8') if user.realname else None,
                            'password': user.password.encode('utf-8') if user.password else None
                           }
        self._save_config(os.path.join(self.path, 'users', user.name), sections)

    def remove_user(self, name):
        os.unlink(os.path.join(self.path, 'users', name))

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
        config = self._get_config(os.path.join(self.path, 'files', hashlib.sha1(f.path).hexdigest()))
        if not config:
            return f

        infos = dict(config.items('infos'))
        f.view = infos.get('view', None)
        for key, value in config.items('perms'):
            f.perms[key] = int(value)
        return f

    def save_file(self, f):
        sections = {}
        sections['infos'] = {'path': f.path,
                             'view': f.view}
        sections['perms'] = f.perms
        self._save_config(os.path.join(self.path, 'files', hashlib.sha1(f.path).hexdigest()), sections)

    def _get_config(self, path):
        config = RawConfigParser()
        try:
            with open(path, 'r') as fp:
                config.readfp(fp)
        except IOError:
            return None
        return config

    def _save_config(self, path, sections):
        config = RawConfigParser()
        for sec, items in sections.iteritems():
            config.add_section(sec)
            for key, value in items.iteritems():
                config.set(sec, key, value)
        with open(path, 'wb') as fp:
            config.write(fp)
