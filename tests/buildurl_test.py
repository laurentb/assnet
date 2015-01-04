from assnet.storage import Storage
from assnet.users import User
from assnet.server import Server
from assnet.template import build_url, build_root_url
from assnet.filters import quote_url

from unittest import TestCase
from webtest import TestApp

from tempfile import mkdtemp
import shutil
import os


class BuildURLTest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='assnet_test_root')
        self.storage = Storage.create(self.root)
        server = Server(self.root)
        app = TestApp(server)
        # fill root_url
        app.get('http://penguin:42/')
        self.root_url = build_root_url(self.storage)

        user = User(self.storage, 'user1')
        user.realname = 'Penguin'
        user.password = 'monkey1'
        user.key = 'fabf37d746da8a45df63489f642b3813'
        user.save()

        user = User(self.storage, 'user2')
        user.realname = 'Penguin'
        user.password = 'monkey1'
        user.save()

    def tearDown(self):
        if self.root:
            shutil.rmtree(self.root)

    def test_buildRootUrl(self):
        assert self.root_url.url == 'http://penguin:42/'
        assert build_root_url(None) is None

    def test_buildSimpleUrl(self):
        assert quote_url(build_url(self.root_url, self.storage.get_file(''))) \
                == 'http://penguin:42/'
        assert quote_url(build_url(self.root_url, self.storage.get_file('/penguin'))) \
                == 'http://penguin:42/penguin'
        # if it is a directory, a trailing / is added
        os.mkdir(os.path.join(self.root, 'penguin'))
        assert quote_url(build_url(self.root_url, self.storage.get_file('/penguin'))) \
                == 'http://penguin:42/penguin/'

    def test_buildKeyUrls(self):
        assert quote_url(build_url(self.root_url,
            self.storage.get_file('/penguin'),
            self.storage.get_user('user1'))) \
                == 'http://penguin:42/penguin?authkey=fabf37d746da8a45df63489f642b3813'

        # no user.key
        assert quote_url(build_url(self.root_url,
            self.storage.get_file('/penguin'),
            self.storage.get_user('user2'))) \
                == 'http://penguin:42/penguin'

        # user.key, but don't want it
        assert quote_url(build_url(self.root_url,
            self.storage.get_file('/penguin'),
            self.storage.get_user('user1'),
            use_key=False)) \
                == 'http://penguin:42/penguin'

    def test_buildHttpAuthUrls(self):
        assert quote_url(build_url(self.root_url,
            self.storage.get_file('/penguin'),
            self.storage.get_user('user1'),
            http_auth=True)) \
                == 'http://_key:fabf37d746da8a45df63489f642b3813@penguin:42/penguin?authby=http'

        # no user.key
        assert quote_url(build_url(self.root_url,
            self.storage.get_file('/penguin'),
            self.storage.get_user('user2'),
            http_auth=True)) \
                == 'http://user2@penguin:42/penguin?authby=http'

        # user.key, but don't want it
        assert quote_url(build_url(self.root_url,
            self.storage.get_file('/penguin'),
            self.storage.get_user('user1'),
            http_auth=True, use_key=False)) \
                == 'http://user1@penguin:42/penguin?authby=http'
