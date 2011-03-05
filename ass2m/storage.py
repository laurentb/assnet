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
from .users import User, Anonymous
from .files import File

class Storage(object):
    def __init__(self, path):
        self.path = path
        self.config = self._get_config(os.path.join(self.path, 'config')) or {}

    def save_config(self):
        self._save_config(os.path.join(self.path, 'config'), self.config)

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
        if config is None:
            return Anonymous()

        user = User(self, name)
        info = config.get('info', {})
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
        config = self._get_config(os.path.join(self.path, 'users', user.name)) or {}
        info = config.setdefault('info', {})
        info['email'] = user.email if user.email else None
        info['realname'] = user.realname if user.realname else None
        info['password'] = user.password if user.password else None

        self._save_config(os.path.join(self.path, 'users', user.name), config)

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
        if config is None:
            return f

        infos = config.get('infos', {})
        f.view = infos.get('view', None)
        for key, value in config.get('perms', {}).iteritems():
            f.perms[key] = int(value)
        return f

    def save_file(self, f):
        sections = self._get_config(os.path.join(self.path, 'files', hashlib.sha1(f.path).hexdigest())) or {}
        infos = sections.setdefault('infos', {})
        infos['path'] = f.path,
        infos['view'] = f.view

        sections['perms'] = f.perms
        self._save_config(os.path.join(self.path, 'files', hashlib.sha1(f.path).hexdigest()), sections)

    def _get_config(self, path):
        config = RawConfigParser()
        try:
            with open(path, 'r') as fp:
                config.readfp(fp)
        except IOError:
            return None

        sections = {}
        for sec in config.sections():
            sections[sec] = dict([(k,v.decode('utf-8')) for k,v in config.items(sec)])

        return sections

    def _save_config(self, path, sections):
        config = RawConfigParser()
        for sec, items in sections.iteritems():
            config.add_section(sec)
            for key, value in items.iteritems():
                if isinstance(value, unicode):
                    value = value.encode('utf-8')
                config.set(sec, key, value)
        with open(path, 'wb') as fp:
            config.write(fp)
