from __future__ import with_statement

from ass2m.ass2m import Ass2m
from ass2m.server import Server, Context

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
        datapath = os.path.join(self.root, 'test_data')
        os.mkdir(datapath)
        os.mkdir(os.path.join(datapath, 'assets'))
        with open(os.path.join(datapath, 'assets', 'main.css'), 'w') as f:
            f.write('body { background-color: pink; }')
        # monkeypatching
        self.data_paths = Context.DATA_PATHS
        Context.DATA_PATHS = [os.path.join(self.root, 'doesnotexist'), datapath]

    def tearDown(self):
        if self.root:
            shutil.rmtree(self.root)
        # demonkeypatching
        Context.DATA_PATHS = self.data_paths

    def test_getAsset(self):
        res = self.app.get('/?action=asset&file=main.css', status=200)
        assert 'body { background-color: pink; }' == res.body

        self.app.get('/?action=asset&file=none.css', status=404)

        self.app.get('/?action=asset&file=../../.ass2m/config', status=412)
