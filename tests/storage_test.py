from ass2m.storage import Storage, GlobalConfig
from ass2m.obj import ConfigDict
from ass2m.files import File
from unittest import TestCase
from tempfile import mkdtemp
import os
import shutil
from time import sleep

class StorageTest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='ass2m_test_root')
        self.storage = Storage(self.root)

    def tearDown(self):
        if self.root:
            shutil.rmtree(self.root)

    def test_create(self):
        pass
        #self.storage.init()

    def test_configDict(self):
        d = ConfigDict()
        d["a"]
        d["b"]["a"]=1
        assert len(d) == 2
        d.cleanup()
        assert len(d) == 1

    def test_saveAndRead(self):
        # GlobalConfig is the simplest storage object
        cfg = GlobalConfig(self.storage)
        assert cfg.exists is None
        cfg.read()
        assert cfg.exists is False
        assert len(cfg.data) == 0
        cfg.data["penguin"]["gentoo"] = 42
        assert isinstance(cfg.data["platypus"], dict)
        assert len(cfg.data) == 2

        cfg.read()
        assert cfg.exists is False
        assert len(cfg.data) == 0
        cfg.save()
        assert cfg.exists is True

        assert len(cfg.data) == 0
        cfg.data["penguin"]["gentoo"] = 42
        cfg.data["platypus"]
        cfg.save()
        assert cfg.exists is True
        assert len(cfg.data) == 1

        cfg.read()
        assert cfg.exists is True
        assert len(cfg.data) == 1
        assert len(cfg.data["penguin"]) == 1

        # completely reload
        cfg = GlobalConfig(self.storage)
        assert cfg.exists is None
        cfg.read()
        assert cfg.exists is True
        assert len(cfg.data) == 1
        assert len(cfg.data["penguin"]) == 1

    def test_createAndRemove(self):
        cfg = GlobalConfig(self.storage)
        assert cfg.exists is None
        cfg.read()
        assert cfg.exists is False
        cfg.save()
        assert cfg.exists is True

        cfg = GlobalConfig(self.storage)
        assert cfg.exists is None
        cfg.read()
        assert cfg.exists is True
        cfg.remove()
        assert cfg.exists is False

        cfg = GlobalConfig(self.storage)
        assert cfg.exists is None
        cfg.read()
        assert cfg.exists is False

    def test_mtime(self):
        cfg = GlobalConfig(self.storage)
        assert cfg._mtime is None
        cfg.read()
        # file does not exist
        assert cfg._mtime is None
        # file is written for the first time
        cfg.save()
        sleep(0.1)
        assert cfg._mtime is not None
        mtime1 = cfg._mtime
        cfg.read()
        # reload file, the file wasn't changed
        assert mtime1 == cfg._mtime
        cfg.data["penguin"]["gentoo"] = 42
        cfg.save()
        sleep(0.1)
        # file changed
        assert mtime1 < cfg._mtime
        mtime2 = cfg._mtime
        cfg.read()
        # file didn't change
        assert mtime2 == cfg._mtime
        cfg.save()
        sleep(0.1)
        # no actual modifications of data, should not have been written
        assert mtime2 == cfg._mtime
