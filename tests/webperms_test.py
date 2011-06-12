from ass2m.storage import Storage
from ass2m.users import User, Group
from ass2m.files import File
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
        user = User(self.storage, 'penguin')
        user.realname = 'Penguin'
        user.password = 'monkey1'
        user.key = 'fabf37d746da8a45df63489f642b3813'
        user.save()
        group = Group('admin')
        group.users = ['penguin']
        groupscfg = self.storage.get_groupscfg()
        groupscfg['admin'] = group
        groupscfg.save()
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
        self._set_perms('/penguins', all=File.PERM_READ | File.PERM_LIST)
        res = self.app.get('/', status=200)
        assert 'penguins' not in res.body
        res = self.app.get('/penguins/', status=200)
        assert 'gentoo' not in res.body
        res = self.app.get('/penguins/gentoo', status=200)
        assert 'HELLO' == res.body

        # force the display of one file in the directory
        self._set_perms('/penguins/gentoo', all=File.PERM_READ | File.PERM_IN)
        res = self.app.get('/penguins/', status=200)
        assert 'gentoo' in res.body

        # deny listing completely, we can still get the file due to its perms
        self._set_perms('/penguins', all=0)
        res = self.app.get('/', status=200)
        assert 'penguins' not in res.body
        res = self.app.get('/penguins/', status=403)
        assert 'gentoo' not in res.body
        res = self.app.get('/penguins/gentoo', status=200)
        assert 'HELLO' == res.body

        res = self.app.get('/?action=login', status=200)
        assert 'Not logged in.' in res.body

        # login
        form = res.form
        form['login[username]'] = 'penguin'
        form['login[password]'] = 'monkey1'
        res = form.submit(status=302)

        # check user perms
        self._set_perms('/penguins', all=0, u_penguin=File.PERM_READ | File.PERM_LIST | File.PERM_IN)
        res = self.app.get('/', status=200)
        assert 'penguins' in res.body
        res = self.app.get('/penguins/', status=200)
        assert 'gentoo' in res.body

        self._set_perms('/penguins', all=0, u_penguin=File.PERM_READ | File.PERM_IN)
        res = self.app.get('/', status=200)
        assert 'penguins' in res.body
        self.app.get('/penguins/', status=403)

        # check group perms
        self._set_perms('/penguins', all=0, g_admin=File.PERM_READ | File.PERM_LIST | File.PERM_IN)
        res = self.app.get('/', status=200)
        assert 'penguins' in res.body
        res = self.app.get('/penguins/', status=200)
        assert 'gentoo' in res.body

        self._set_perms('/penguins', all=0, g_admin=File.PERM_READ | File.PERM_IN)
        res = self.app.get('/', status=200)
        assert 'penguins' in res.body
        self.app.get('/penguins/', status=403)

        # check recursive perms
        self._set_perms('/', all=0, g_admin=File.PERM_LIST | File.PERM_READ | File.PERM_IN)
        self._set_perms('/penguins')
        res = self.app.get('/penguins/', status=200)
        assert 'gentoo' in res.body

        self._set_perms('/', all=File.PERM_LIST | File.PERM_READ | File.PERM_IN, g_admin=0)
        self.app.get('/penguins/', status=403)

        self._set_perms('/', all=File.PERM_LIST | File.PERM_READ | File.PERM_IN, u_penguins=0)
        self._set_perms('/penguins', g_admin=File.PERM_LIST | File.PERM_READ | File.PERM_IN)
        self.app.get('/penguins/', status=200)

    def _set_perms(self, path, **perms):
        f = self.storage.get_file(path)
        f.perms = {}
        for name, perm in perms.iteritems():
            f.perms[name.replace('_', '.')] = perm
        f.save()
