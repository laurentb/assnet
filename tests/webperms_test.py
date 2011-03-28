from __future__ import with_statement

from ass2m.storage import Storage
from ass2m.server import Server

from unittest import TestCase
from webtest import TestApp

from tempfile import mkdtemp
import shutil
import os

class WebPermsTest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='ass2m_test_root')
        self.storage = Storage.create(self.root)
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

    def test_list(self):
        os.mkdir(os.path.join(self.root, 'penguins'))
        with open(os.path.join(self.root, 'penguins', 'gentoo'), 'w') as f:
            f.write('HELLO')

        # default perms
        res = self.app.get('/', status=200)
        assert 'penguins' in res.body
        res = self.app.get('/penguins/', status=200)
        assert 'gentoo' in res.body
        res = self.app.get('/penguins/gentoo', status=200)
        assert 'HELLO' == res.body

        # files are hidden, but it is still possible do download them if we know the URL
        f = self.storage.get_file('/penguins')
        f.perms = {'all': f.PERM_READ}
        f.save()
        res = self.app.get('/', status=200)
        assert 'penguins' not in res.body
        res = self.app.get('/penguins/', status=200)
        assert 'gentoo' not in res.body
        res = self.app.get('/penguins/gentoo', status=200)
        assert 'HELLO' == res.body

        # force the display of one file in the directory
        f = self.storage.get_file('/penguins/gentoo')
        f.perms = {'all': f.PERM_READ|f.PERM_LIST}
        f.save()
        res = self.app.get('/penguins/', status=200)
        assert 'gentoo' in res.body

        # deny listing completely, we can still get the file due to its perms
        f = self.storage.get_file('/penguins')
        f.perms = {'all': 0}
        f.save()
        res = self.app.get('/', status=200)
        assert 'penguins' not in res.body
        res = self.app.get('/penguins/', status=403)
        assert 'gentoo' not in res.body
        res = self.app.get('/penguins/gentoo', status=200)
        assert 'HELLO' == res.body
