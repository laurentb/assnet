# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import hashlib
from ConfigParser import RawConfigParser

class User(object):
    def __init__(self, name):
        self.name = name
        self.email = None

class Group(object):
    def __init__(self, name):
        self.name = name
        self.users = []

class File(object):
    def __init__(self, path):
        self.path = path
        self.perms = {}

class Storage(object):
    def __init__(self, path):
        self.path = path

    @classmethod
    def init(cls, path):
        os.mkdir(path)
        os.mkdir(os.path.join(path, 'users'))
        os.mkdir(os.path.join(path, 'files'))
        return cls(path)

    def get_user(self, name):
        config = self._get_config(os.path.join(self.path, 'users', name))
        if not config:
            return None

        user = User(name)
        info = dict(config.items('info'))
        user.email = info.get('email', None)
        return user

    def save_user(self, user):
        sections = {}
        sections['info'] = {'email': user.email}
        self._save_config(os.path.join(self.path, 'users', user.name), sections)

    def get_file(self, path):
        config = self._get_config(os.path.join(self.path, 'files', hashlib.sha1(path).hexdigest()))
        if not config:
            return None

        f = File(path)
        return f

    def save_file(self, f):
        sections = {}
        self._save_config(os.path.join(self.path, 'files', hashlib.sha1(f.path).hexdigest()), sections)

    def _get_config(self, path):
        config = RawConfigParser()
        try:
            with open(path, 'r') as f:
                config.readfp(f)
        except IOError:
            return None
        return config

    def _save_config(self, path, sections):
        config = RawConfigParser()
        for sec, items in sections.iteritems():
            config.add_section(sec)
            for key, value in items.iteritems():
                config.set(sec, key, unicode(value))
        with open(path, 'wb') as f:
            config.write(f)
