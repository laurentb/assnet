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

    @classmethod
    def create(cls, path):
        return cls(Storage.init(os.path.join(path, cls.DIRNAME)))
