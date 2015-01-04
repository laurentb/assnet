from assnet.storage import Storage
from assnet.server import Server

from unittest import TestCase
from webtest import TestApp

from tempfile import mkdtemp
import os
import shutil


class AssetsTest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='assnet_test_root')
        Storage.create(self.root)
        server = Server(self.root)
        self.app = TestApp(server)
        datapath = os.path.join(self.root, 'test_data')
        os.mkdir(datapath)
        os.mkdir(os.path.join(datapath, 'assets'))
        with open(os.path.join(datapath, 'assets', 'main.css'), 'w') as f:
            f.write('body { background-color: pink; }')
        # monkeypatching
        self.data_paths = Storage.DATA_PATHS
        Storage.DATA_PATHS.insert(0, datapath)
        Storage.DATA_PATHS.insert(0, os.path.join(self.root, 'doesnotexist'))

    def tearDown(self):
        if self.root:
            shutil.rmtree(self.root)
        # demonkeypatching
        Storage.DATA_PATHS = self.data_paths

    def test_getAsset(self):
        res = self.app.get('/?action=asset&file=main.css', status=200)
        assert 'body { background-color: pink; }' == res.body

        self.app.get('/?action=asset&file=none.css', status=404)

        self.app.get('/?action=asset&file=../../.assnet/config', status=412)

    def test_stylesheets(self):
        res = self.app.get('/?view=list', status=200)
        assert '<link rel="stylesheet" type="text/css" href="/?action=asset&amp;file=main.css" />' in res.body

        res = self.app.get('/test_data/?view=medialist', status=200)
        assert '<link rel="stylesheet" type="text/css" href="/?action=asset&amp;file=main.css" />' in res.body
