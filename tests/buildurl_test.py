from ass2m.storage import Storage
from ass2m.server import Server
from ass2m.template import build_url, build_root_url
from ass2m.filters import quote_url

from unittest import TestCase
from webtest import TestApp

from tempfile import mkdtemp
import shutil
import os


class BuildURLTest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='ass2m_test_root')
        self.storage = Storage.create(self.root)
        server = Server(self.root)
        app = TestApp(server.process)
        # fill root_url
        app.get('http://penguin:42/')
        self.root_url = build_root_url(self.storage)

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
