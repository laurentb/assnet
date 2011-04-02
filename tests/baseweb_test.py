from __future__ import with_statement

from ass2m.storage import Storage
from ass2m.server import Server

from unittest import TestCase
from webtest import TestApp

from tempfile import mkdtemp
import os
import shutil

class BaseWebTest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='ass2m_test_root')
        Storage.create(self.root)
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

        res = self.app.get("/penguins?view=list", status=302)
        assert res.location == "http://localhost/penguins/?view=list"
        res.follow(status=200)

        # no trailing slash for files
        res = self.app.get("/penguins/gentoo", status=200)

        res = self.app.get("/penguins/gentoo/", status=302)
        assert res.location == "http://localhost/penguins/gentoo"
        res.follow(status=200)

        res = self.app.get("/penguins/gentoo/?view=raw", status=302)
        assert res.location == "http://localhost/penguins/gentoo?view=raw"
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

    def test_listWithParent(self):
        os.mkdir(os.path.join(self.root, "penguins"))
        res = self.app.get("/", status=200)
        assert "Parent directory" not in res.body
        res = self.app.get("/penguins/", status=200)
        assert "Parent directory" in res.body
        res = res.click("Parent directory")
        assert "<h1>Index of /</h1>" in res.body

    def test_actionsInRoot(self):
        os.mkdir(os.path.join(self.root, 'penguins'))
        with open(os.path.join(self.root, 'penguins', 'gentoo'), 'w') as f:
            f.write('HELLO')
        res = self.app.get('/?action=login', status=200)
        assert 'penguins' not in res.body
        res = self.app.get('/?foo=bar&action=login', status=200)
        assert 'penguins' not in res.body
        self.app.get('/doesnotexist?action=login', status=404)
        self.app.get('/doesnotexist/?action=login', status=404)
        res = self.app.get('/penguins/?action=login', status=200)
        assert 'gentoo' in res.body
        res = self.app.get('/penguins/gentoo?action=login', status=200)
        assert 'HELLO' == res.body

    def test_methods(self):
        self.app._gen_request('HEAD', '/?view=text_list', status=200)
        self.app.get('/?view=text_list', status=200)
        self.app.post('/?view=text_list', status=405)
        self.app.put('/?view=text_list', status=405)
        self.app.delete('/?view=text_list', status=405)

        self.app.get('/?action=logout', status=302)
        self.app.post('/?action=logout', status=405)

        self.app.get('/?action=login', status=200)
        self.app.post('/?action=login', status=200)
        self.app.post('/?action=login', {'_method': 'DELETE'}, status=405)

        self.app.post('/?_method=GET', status=405)
        self.app.post('/?action=login', {'_method': 'HEAD'}, status=405)
