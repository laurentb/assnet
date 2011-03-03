from __future__ import with_statement

from ass2m.ass2m import Ass2m
from ass2m.server import Server

from unittest import TestCase
from webtest import TestApp

from tempfile import mkdtemp
import os.path
import shutil

class BaseWebTest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='ass2m_test_root')
        ass2m = Ass2m(self.root)
        ass2m.create(self.root)
        server = Server(self.root)
        self.app = TestApp(server.process)

    def tearDown(self):
        if self.root:
            shutil.rmtree(self.root)

    def test_listAndDownload(self):
        res = self.app.get("/")
        assert "<h1>Index of /</h1>" in res.body

        with file(os.path.join(self.root, "penguins_are_cute"), 'a') as f:
            f.write("HELLO")

        res = self.app.get("/")
        assert "penguins_are_cute" in res.body

        res = self.app.get("/penguins_are_cute")
        assert "HELLO" == res.body

