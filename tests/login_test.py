from __future__ import with_statement

from ass2m.ass2m import Ass2m
from ass2m.server import Server
from ass2m.users import User

from unittest import TestCase
from webtest import TestApp

from tempfile import mkdtemp
import shutil

class LoginTest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='ass2m_test_root')
        ass2m = Ass2m(self.root)
        ass2m.create(self.root)
        user = User(ass2m.storage, 'penguin')
        user.realname = 'Penguin'
        user.password = 'monkey1'
        user.save()
        server = Server(self.root)
        self.app = TestApp(server.process)

    def tearDown(self):
        if self.root:
            shutil.rmtree(self.root)

    def test_defaultDirs(self):
        res = self.app.get('/?action=login', status=200)
        assert 'Current user: &lt;anonymous&gt;' in res.body

        form = res.form
        form['username'] = 'invalid'
        form['password'] = 'invalid'
        res = form.submit()
        assert 'Current user: &lt;anonymous&gt;' in res.body

        form = res.form
        form['username'] = 'penguin'
        form['password'] = 'invalid'
        res = form.submit()
        assert 'Current user: &lt;anonymous&gt;' in res.body

        form = res.form
        form['username'] = 'penguin'
        form['password'] = 'monkey1'
        res = form.submit(status=302)
        res = res.follow(status=200)
        assert 'Current user: penguin' in res.body
