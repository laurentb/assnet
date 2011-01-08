# -*- coding: utf-8 -*-

import os

class WorkdirNotFound(Exception): pass

class Ass2m(object):
    DIRNAME = '.ass2m'

    def __init__(self, path):
        while not self.DIRNAME in os.listdir(path) and path != os.path.dirname(path):
            path = os.path.dirname(path)
        if path == os.path.dirname(path):
            raise WorkdirNotFound()

        self.workdir = os.path.join(path, self.DIRNAME)

    @classmethod
    def create(cls, path):
        os.mkdir(os.path.join(path, cls.DIRNAME))
        return cls(path)
