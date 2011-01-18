# -*- coding: utf-8 -*-

import os
from storage import Storage

class NotWorkingDir(Exception): pass

class Ass2m(object):
    DIRNAME = '.ass2m'

    def __init__(self, path):
        if isinstance(path, Storage):
            storage = path
        else:
            while not self.DIRNAME in os.listdir(path) and path != os.path.dirname(path):
                path = os.path.dirname(path)
            if path == os.path.dirname(path):
                raise NotWorkingDir()

            storage = Storage(os.path.join(path, self.DIRNAME))
        self.storage = storage
        self.root = os.path.realpath(os.path.join(storage.path, os.path.pardir))

    @classmethod
    def create(cls, path):
        return cls(Storage.init(os.path.join(path, cls.DIRNAME)))

    def get_file(self, name):
        return self.storage.get_file(name)

    def get_user(self, name):
        return self.storage.get_user(name)
