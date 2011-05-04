from ass2m.storage import Storage
from ass2m.server import Server
from ass2m.users import User

from unittest import TestCase
from webtest import TestApp

from tempfile import mkdtemp
import shutil


class LoginTest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='ass2m_test_root')
        storage = Storage.create(self.root)
        user = User(storage, 'penguin')
        user.realname = 'Penguin'
        user.password = 'monkey1'
        user.key = 'fabf37d746da8a45df63489f642b3813'
        user.save()
        user = User(storage, 'platypus')
        user.realname = 'Platypus'
        user.save()
        server = Server(self.root)
        self.app = TestApp(server.process)

    def tearDown(self):
        if self.root:
            shutil.rmtree(self.root)

    def test_formLogin(self):
        res = self.app.get('/?action=login', status=200)
        assert 'Not logged in.' in res.body
        assert 'Invalid username or password.' not in res.body
        assert 'Logged as.' not in res.body

        form = res.form
        form['login[username]'] = 'invalid'
        form['login[password]'] = 'invalid'
        res = form.submit()
        assert 'Not logged in.' not in res.body
        assert 'Invalid username or password.' in res.body
        assert 'Logged as.' not in res.body

        form = res.form
        form['login[username]'] = 'penguin'
        form['login[password]'] = 'invalid'
        res = form.submit()
        assert 'Not logged in.' not in res.body
        assert 'Invalid username or password.' in res.body
        assert 'Logged as.' not in res.body

        form = res.form
        form['login[username]'] = 'penguin'
        form['login[password]'] = 'monkey1'
        res = form.submit(status=302)
        res = res.follow(status=200)
        assert 'Logged as <abbr title="Penguin">penguin</abbr>' in res.body
        res = self.app.get('/?action=login', status=200)
        assert 'Not logged in.' not in res.body
        assert 'Invalid username or password.' not in res.body
        assert 'Already logged in as <abbr title="Penguin">penguin</abbr>' in res.body

        res = self.app.get('/')
        assert 'Login' not in res.body
        assert 'Logged as <abbr title="Penguin">penguin</abbr>' in res.body
        res = self.app.get('/?action=logout', status=302)
        res = res.follow(status=200)
        assert 'Login' in res.body
        assert 'Logged as' not in res.body

    def test_authKeyLogin(self):
        res = self.app.get('/?action=login', status=200)
        assert 'Not logged in.' in res.body

        # we are authentified by the key
        res = self.app.get('/?authkey=fabf37d746da8a45df63489f642b3813', status=200)
        assert 'Login' not in res.body
        assert 'Logged as <abbr title="Penguin">penguin</abbr>' in res.body

        # the authentification is kept
        res = self.app.get('/', status=200)
        assert 'Login' not in res.body
        assert 'Logged as <abbr title="Penguin">penguin</abbr>' in res.body
        res = self.app.get('/?action=logout', status=302)
        res = res.follow(status=200)
        assert 'Login' in res.body
        assert 'Logged as' not in res.body
