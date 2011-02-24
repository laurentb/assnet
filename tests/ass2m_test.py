from ass2m.ass2m import Ass2m
from unittest import TestCase
from tempfile import mkdtemp
import os
import shutil

class Ass2mTest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='ass2m_test_root')

    def tearDown(self):
        if self.root:
            shutil.rmtree(self.root)

    def test_createAndLoad(self):
        # test creation
        ass2m = Ass2m(self.root)
        assert ass2m.storage is None
        assert ass2m.root is None
        ass2m.create(self.root)
        assert ass2m.storage is not None
        assert ass2m.root is not None
        assert os.path.isdir(ass2m.root)
        assert os.path.samefile(ass2m.root, self.root)
        assert isinstance(ass2m.storage.config, dict)

        # test loading of an existing dir
        ass2m = Ass2m(self.root)
        assert ass2m.storage is not None
        assert ass2m.root is not None
        assert os.path.samefile(ass2m.root, self.root)
        assert isinstance(ass2m.storage.config, dict)

    def test_globalConfig(self):
        # create and set settings
        ass2m = Ass2m(self.root)
        ass2m.create(self.root)
        ass2m.storage.config.setdefault("penguins", {})["cute"] = "yes"
        ass2m.storage.save_config()

        # were they saved properly?
        ass2m = Ass2m(self.root)
        assert ass2m.storage.config.setdefault("penguins", {}).get("cute") == "yes"

