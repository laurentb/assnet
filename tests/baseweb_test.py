from __future__ import with_statement

from ass2m.ass2m import Ass2m
from ass2m.server import Server

from unittest import TestCase
from webtest import TestApp

from tempfile import mkdtemp
import os
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

        with open(os.path.join(self.root, "penguins_are_cute"), 'w') as f:
            f.write("HELLO")

        res = self.app.get("/")
        assert "penguins_are_cute" in res.body

        res = self.app.get("/penguins_are_cute")
        assert "HELLO" == res.body

    def test_pathNormalization(self):
        os.mkdir(os.path.join(self.root, "penguins"))
        with open(os.path.join(self.root, "penguins", "gentoo"), 'w') as f:
            f.write("The best penguin.")

        # trailing slash for directories
        res = self.app.get("/penguins/", status=200)

        res = self.app.get("/penguins", status=302)
        assert res.location == "http://localhost/penguins/"
        res.follow(status=200)

        res = self.app.get("/penguins?action=list", status=302)
        assert res.location == "http://localhost/penguins/?action=list"
        res.follow(status=200)

        # no trailing slash for files
        res = self.app.get("/penguins/gentoo", status=200)

        res = self.app.get("/penguins/gentoo/", status=302)
        assert res.location == "http://localhost/penguins/gentoo"
        res.follow(status=200)

        res = self.app.get("/penguins/gentoo/?action=download", status=302)
        assert res.location == "http://localhost/penguins/gentoo?action=download"
        res.follow(status=200)

        # limit cases
        res = self.app.get("/", status=200)

        res = self.app.get("//", status=302)
        assert res.location == "http://localhost/"
        res.follow(status=200)

        # more sanitization
        res = self.app.get("/penguins///", status=302)
        assert res.location == "http://localhost/penguins/"
        res.follow(status=200)
        res = self.app.get("/penguins/..//..", status=302)
        assert res.location == "http://localhost/"
        res.follow(status=200)
        res = self.app.get("/../", status=302)
        assert res.location == "http://localhost/"
        res.follow(status=200)
        res = self.app.get(r"/penguins\..\penguins/..", status=302)
        assert res.location == "http://localhost/"
        res.follow(status=200)
        res = self.app.get(r"/penguins\\\gentoo\\", status=302)
        assert res.location == "http://localhost/penguins/gentoo"
        res.follow(status=200)


    def test_notFound(self):
        self.app.get("/penguins/", status=404)
        self.app.get("/penguins", status=404)
