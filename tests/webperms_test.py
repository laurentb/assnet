from __future__ import with_statement

from ass2m.ass2m import Ass2m
from ass2m.server import Server

from unittest import TestCase
from webtest import TestApp

from tempfile import mkdtemp
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

    def test_defaultDirs(self):
        # list the root directory
        res = self.app.get("/", status=200)
        # hide the ass2m dir
        assert ".ass2m" not in res.body
        # don't list the ass2m dir
        res = self.app.get("/.ass2m/", status=403)

        # don't normalize the path
        res = self.app.get("/.ass2m", status=403)
        # don't serve the file
        res = self.app.get("/.ass2m/config", status=403)
        # don't 404
        res = self.app.get("/.ass2m/penguin", status=403)
