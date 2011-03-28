from unittest import TestCase
from ass2m.cli import CLI
from ass2m.storage import Storage
from ass2m.users import User
from tempfile import mkdtemp
import os
import re
import shutil
import sys
from StringIO import StringIO

class BaseCLITest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='ass2m_test_root')
        self.app = CLI(self.root)

    def tearDown(self):
        if self.root:
            shutil.rmtree(self.root)

    def beginCapture(self):
        self.stdout = sys.stdout
        # begin capture
        sys.stdout = StringIO()

    def endCapture(self):
        captured = sys.stdout
        # end capture
        sys.stdout = self.stdout
        self.stdout = None
        return captured.getvalue()

    def test_init(self):
        self.beginCapture()
        assert self.app.main(['ass2m_test', 'init']) in (0, None)
        output = self.endCapture()
        assert output.strip() == "Ass2m working directory created."

        self.beginCapture()
        assert self.app.main(['ass2m_test', 'tree']) in (0, None)
        output = self.endCapture()
        assert re.match(re.escape(r'/')+r'\s+'+re.escape(r'all(rl-)'), output, re.S)
        assert re.match(".+"+re.escape(r'/.ass2m/')+r'\s+'+re.escape(r'all(---)'), output, re.S)

    def test_findRoot(self):
        self.beginCapture()
        assert self.app.main(['ass2m_test', 'init']) in (0, None)
        self.endCapture()

        subdir = os.path.join(self.root, "penguins")
        os.mkdir(subdir)
        subapp = CLI(subdir)
        assert subapp.main(['ass2m_test', 'tree']) in (0, None)

    def test_genKey(self):
        self.beginCapture()
        assert self.app.main(['ass2m_test', 'init']) in (0, None)
        self.endCapture()

        storage = Storage.lookup(self.root)
        user = User(storage, 'penguin')
        user.realname = 'Penguin'
        user.password = 'monkey1'
        user.save()

        self.beginCapture()
        assert self.app.main(['ass2m_test', 'contacts', 'genkey', 'penguin']) in (0, None)
        output = self.endCapture()
        assert 'Key of user penguin set' in output
