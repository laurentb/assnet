from __future__ import with_statement

from ass2m.storage import Storage
from ass2m.server import Server

from unittest import TestCase
from webtest import TestApp

from tempfile import mkdtemp
import os
import shutil
import json
from datetime import datetime

class ApiTest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='ass2m_test_root')
        Storage.create(self.root)
        server = Server(self.root)
        self.app = TestApp(server.process)

        with open(os.path.join(self.root, 'penguins_are_cute'), 'w') as f:
            f.write('HELLO')
        os.mkdir(os.path.join(self.root, 'penguins'))
        os.mkdir(os.path.join(self.root, 'empty'))
        with open(os.path.join(self.root, 'penguins', 'gentoo'), 'w') as f:
            f.write('The best penguin.')
        with open(os.path.join(self.root, 'penguins', 'emperor'), 'w') as f:
            f.write('Another kind of penguin. But it is not the best.')

    def tearDown(self):
        if self.root:
            shutil.rmtree(self.root)

    def test_jsonList(self):
        res = self.app.get('/?view=json_list', status=200)
        data = json.loads(res.body)
        assert len(data) > 0
        assert len(data['files']) == 3
        assert data['files']['penguins']['type'] == 'directory'
        assert data['files']['penguins_are_cute']['type'] == 'file'

        res = self.app.get('/empty/?view=json_list', status=200)
        data = json.loads(res.body)
        assert len(data) > 0
        assert len(data['files']) == 0

    def test_textList(self):
        res = self.app.get('/?view=text_list', status=200)
        assert len(res.body.split('\n')) == 3

        res = self.app.get('/empty/?view=text_list', status=200)
        assert len(res.body) == 0

    def test_jsonInfo(self):
        # info on a directory
        res = self.app.get('/?action=info&view=json_info', status=200)
        data = json.loads(res.body)
        assert data['type'] == 'directory'
        assert data['size'] == None
        assert datetime.strptime(data['mtime'], '%Y-%m-%dT%H:%M:%S').year > 0

        # info on a file
        res = self.app.get('/penguins/gentoo?action=info&view=json_info', status=200)
        data = json.loads(res.body)
        assert data['type'] == 'file'
        assert data['size'] == 17
        assert datetime.strptime(data['mtime'], '%Y-%m-%dT%H:%M:%S').year > 0
