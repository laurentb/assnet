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
        self.storage = Storage(os.path.join(self.root, Storage.DIRNAME))

    def tearDown(self):
        if self.root:
            shutil.rmtree(self.root)

    def test_create(self):
        storage = Storage.create(self.root)
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

    def test_getChildren(self):
        os.mkdir(os.path.join(self.root, 'penguins'))
        with open(os.path.join(self.root, 'penguins', 'gentoo'), 'w') as f:
            f.write('')
        with open(os.path.join(self.root, 'penguins', 'emperor'), 'w') as f:
            f.write('')
        with open(os.path.join(self.root, 'penguins', 'king'), 'w') as f:
            f.write('')

        f = self.storage.get_file('')
        assert f.path == ''
        assert f.get_name() == ''
        assert f.isdir()
        assert not f.isfile()
        children = list(f.iter_children())
        assert len(children) == 1

        f = children[0]
        assert f.path == '/penguins'
        assert f.get_name() == 'penguins'
        assert f.isdir()
        assert not f.isfile()
        children = list(f.iter_children())
        assert len(children) == 3

        f = children[0]
        assert f.path == '/penguins/emperor'
        assert f.get_name() == 'emperor'
        assert f.isfile()
        assert not f.isdir()

        f = f.parent()
        assert f.path == '/penguins'
        assert f.get_name() == 'penguins'
        assert f.isdir()
        assert not f.isfile()

        f = f.parent()
        assert f.path == ''
        assert f.get_name() == ''
        assert f.isdir()
        assert not f.isfile()

        f = f.parent()
        assert f is None

    def test_getAttrs(self):
        os.mkdir(os.path.join(self.root, 'penguins'))
        with open(os.path.join(self.root, 'penguins', 'gentoo'), 'w') as f:
            f.write('The best penguin.')
        with open(os.path.join(self.root, 'penguins', 'emperor'), 'w') as f:
            f.write('')

        f = self.storage.get_file('')
        assert f.get_mtime().year > 0

        f = self.storage.get_file('/penguins/gentoo')
        assert f.get_size() == 17
        assert f.get_mtime().year > 0
        assert f.get_human_size() == '17.0 B'

        f = self.storage.get_file('/penguins/emperor')
        assert f.get_size() == 0
        assert f.get_mtime().year > 0
        assert f.get_human_size() == '0 B'

    def test_getHumanSize(self):
        class Chafouin(File):
            def __init__(self, fakesize):
                self.fakesize = fakesize
            def get_size(self):
                return self.fakesize

        assert Chafouin(1).get_human_size() == '1.0 B'
        assert Chafouin(1024).get_human_size() == '1.0 KiB'
        assert Chafouin(4*1024+128).get_human_size() == '4.1 KiB'
        assert Chafouin(4*1024*1024).get_human_size() == '4.0 MiB'
        assert Chafouin(42*1024*1024*1024).get_human_size() == '42.0 GiB'
