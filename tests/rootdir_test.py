from assnet.storage import Storage
from assnet.server import Server

from unittest import TestCase
from webtest import TestApp

from tempfile import mkdtemp
import os
import shutil


class RootDirTest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='assnet_test_root')
        with open(os.path.join(self.root, "penguin"), 'w') as f:
            f.write("HELLO")
        self.a_wd = os.path.join(self.root, 'a_wd')
        self.not_a_wd = os.path.join(self.root, 'not_a_wd')
        os.mkdir(self.a_wd)
        os.mkdir(self.not_a_wd)
        Storage.create(self.a_wd)

    def tearDown(self):
        if self.root:
            shutil.rmtree(self.root)

    def test_notWorkingDir(self):
        server = Server(self.root)
        app = TestApp(server)
        res = app.get("/", status=500)
        assert "not an assnet working directory" in res.body
        res = app.get("/penguin", status=500)
        assert "not an assnet working directory" in res.body
        res = app.get("/penguins", status=500)
        assert "not an assnet working directory" in res.body

    def test_noRootPath(self):
        server = Server(None)
        app = TestApp(server)
        res = app.get("/", status=500)
        assert "No root path was provided" in res.body
        res = app.get("/penguin", status=500)
        assert "No root path was provided" in res.body
        res = app.get("/penguins", status=500)
        assert "No root path was provided" in res.body

    def test_configByEnv(self):
        server = Server(None)
        app = TestApp(server)
        res = app.get("/", status=500, extra_environ={'ASSNET_ROOT': self.root})
        assert "not an assnet working directory" in res.body
        Storage.create(self.root)
        res = app.get("/", status=200, extra_environ={'ASSNET_ROOT': self.not_a_wd})
        assert "penguin" in res.body
        res = app.get("/penguin", status=200, extra_environ={'ASSNET_ROOT': self.not_a_wd})
        assert "HELLO" == res.body

        res = app.get("/", status=200, extra_environ={'ASSNET_ROOT': self.a_wd})
        assert "penguin" not in res.body
        res = app.get("/penguin", status=404, extra_environ={'ASSNET_ROOT': self.a_wd})

        server = Server(self.a_wd)
        app = TestApp(server)
        res = app.get("/", status=200)
        res = app.get("/", status=200, extra_environ={'ASSNET_ROOT': self.root})
        assert "penguin" in res.body
        res = app.get("/penguin", status=404)
        res = app.get("/penguin", status=200, extra_environ={'ASSNET_ROOT': self.root})
        assert "HELLO" == res.body
