# -*- coding: utf-8 -*-

from __future__ import with_statement

import os

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
        config = self._get_config(os.path.join(path, 'users', name))
        if not config:
            return None

        user = User(name)
        info = dict(config.items('info'))
        user.email = info.get('email', None)
        return user

    def _get_config(self, path):
        config = RawConfigParser()
        try:
            with open(path, 'r') as f:
                config.readfp(f)
        except IOError:
            return None
        return config
