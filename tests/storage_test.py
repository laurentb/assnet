from ass2m.storage import Storage, GlobalConfig
from ass2m.obj import ConfigDict
from ass2m.files import File
from ass2m.users import User
from unittest import TestCase
from tempfile import mkdtemp
import shutil
import os

class StorageTest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='ass2m_test_root')
        self.storage = Storage(os.path.join(self.root, 'store'))

    def tearDown(self):
        if self.root:
            shutil.rmtree(self.root)

    def test_create(self):
        storage = Storage.init(os.path.join(self.root, 'store'))
        assert len(storage.get_file('').perms) == 1
        assert len(storage.get_file('/.ass2m').perms) == 1

    def test_configDict(self):
        d = ConfigDict()
        d['a']
        d['b']['a']=1
        assert len(d) == 2
        d.cleanup()
        assert len(d) == 1

    def test_saveAndRead(self):
        # GlobalConfig is the simplest storage object
        cfg = GlobalConfig(self.storage)
        assert cfg.exists is None
        cfg.read()
        assert cfg.exists is False
        assert len(cfg.data) == 0
        cfg.data['penguin']['gentoo'] = u"42"
        assert isinstance(cfg.data['platypus'], dict)
        assert len(cfg.data) == 2

        cfg.read()
        assert cfg.exists is False
        assert len(cfg.data) == 0
        cfg.save()
        assert cfg.exists is True

        assert len(cfg.data) == 0
        cfg.data['penguin']['gentoo'] = u"42"
        cfg.data['platypus']
        cfg.save()
        assert cfg.exists is True
        assert len(cfg.data) == 1

        cfg.read()
        assert cfg.exists is True
        assert len(cfg.data) == 1
        assert len(cfg.data['penguin']) == 1

        # completely reload
        cfg = GlobalConfig(self.storage)
        assert cfg.exists is None
        cfg.read()
        assert cfg.exists is True
        assert len(cfg.data) == 1
        assert len(cfg.data['penguin']) == 1

    def test_createAndRemove(self):
        cfg = GlobalConfig(self.storage)
        assert cfg.exists is None
        cfg.read()
        assert cfg.exists is False
        cfg.save()
        assert cfg.exists is True

        cfg = GlobalConfig(self.storage)
        assert cfg.exists is None
        cfg.read()
        assert cfg.exists is True
        cfg.remove()
        assert cfg.exists is False

        cfg = GlobalConfig(self.storage)
        assert cfg.exists is None
        cfg.read()
        assert cfg.exists is False

    def test_readWriteCache(self):
        cfg = GlobalConfig(self.storage)
        assert cfg._mtime is None
        cfg.read()
        # file does not exist
        assert cfg._mtime is None
        # file is written for the first time
        cfg.save()
        assert cfg._mtime is not None
        mtime1 = cfg._mtime
        cfg.read()
        # reload file, the file wasn't changed
        assert mtime1 == cfg._mtime
        cfg.data['penguin']['gentoo'] = u"42"
        cfg.save()
        # cheat to avoid issues with too close mtimes
        mtime = cfg._mtime + 1000
        os.utime(os.path.join(self.storage.path, cfg._get_confname()), (mtime, mtime))
        # file changed
        cfg.read()
        assert mtime1 < cfg._mtime
        mtime2 = cfg._mtime
        cfg.read()
        # file didn't change
        assert mtime2 == cfg._mtime
        cfg.save()
        # no actual modifications of data, should not have been written
        assert mtime2 == cfg._mtime
        # alter the same file via another object
        cfg2 = GlobalConfig(self.storage)
        cfg2.read()
        cfg2.data['penguin']['gentoo'] = u"1337"
        cfg2.save()
        # cheat to avoid issues with too close mtimes
        mtime = cfg2._mtime + 2000
        os.utime(os.path.join(self.storage.path, cfg2._get_confname()), (mtime, mtime))
        cfg.read()
        # file was properly reloaded
        assert cfg._mtime > cfg2._mtime
        assert cfg.data['penguin'].get('gentoo') == u"1337"
        # cheat: alter the mtime of the saved file
        cfg2.data['penguin']['gentoo'] = u"666"
        cfg2.save()
        mtime = cfg2._mtime - 9000
        os.utime(os.path.join(self.storage.path, cfg._get_confname()), (mtime, mtime))
        cfg.read()
        # the file was NOT reloaded
        assert cfg.data['penguin'].get('gentoo') == u"1337"

    def test_filePreAndPost(self):
        f = File(self.storage, '/penguin')
        f.perms['all'] = File.PERM_READ|File.PERM_LIST
        f.view = 'html'
        f.save()

        f = File(self.storage, '/penguin')
        f.read()
        assert f.perms['all'] == File.PERM_READ|File.PERM_LIST
        assert f.view == 'html'
        f.remove()
        assert len(f.perms) == 0
        assert f.view is None

    def test_userPreAndPost(self):
        u = User(self.storage, 'penguin')
        u.realname = 'Penguin'
        u.save()

        u = User(self.storage, 'penguin')
        u.read()
        assert u.realname == 'Penguin'
        u.remove()
        assert u.realname is None

    def test_fileStorage(self):
        f = File(self.storage, '/penguin')
        f.view = 'html'
        f.save()

        f = self.storage.get_file('/penguin')
        assert f.view == 'html'
        f.remove()

        f = self.storage.get_file('/penguin')
        assert f.view is None

    def test_userStorage(self):
        # no users
        assert len(list(self.storage.iter_users())) == 0
        u = self.storage.get_user('penguin')
        # we got the Anonymous user
        assert not hasattr(u, 'save')

        u = User(self.storage, 'penguin')
        u.realname = 'Penguin'
        u.save()

        u = self.storage.get_user('penguin')
        # real User
        assert hasattr(u, 'save')
        assert u.realname == 'Penguin'

        # one user
        assert len(list(self.storage.iter_users())) == 1

        u.remove()
        assert len(list(self.storage.iter_users())) == 0

    def test_configStorage(self):
        c = self.storage.get_config()
        c.data['penguin']['gentoo'] = u"42"
        c.save()

        c = self.storage.get_config()
        assert c.data['penguin'].get('gentoo') == u"42"

    def test_getDiskFile(self):
        f = self.storage.get_file('/penguin')
        f.view = 'html'
        f.save()

        path = os.path.join(self.root, 'penguin')
        f = self.storage.get_file_from_realpath(path)
        assert f.view == 'html'
        assert f.path == '/penguin'
