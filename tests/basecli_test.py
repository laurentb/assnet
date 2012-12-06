from unittest import TestCase
from assnet.cli import CLI
from assnet.storage import Storage
from assnet.users import User
from tempfile import mkdtemp
import os
import re
import shutil
import sys
from StringIO import StringIO


class BaseCLITest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='assnet_test_root')
        self.app = CLI(self.root)

    def tearDown(self):
        if self.root:
            shutil.rmtree(self.root)

    def beginCapture(self, with_stderr=False):
        self.stdout = sys.stdout
        # begin capture
        sys.stdout = StringIO()
        if with_stderr:
            self.stderr = sys.stderr
            sys.stderr = sys.stdout
        elif not hasattr(self, 'stderr'):
            self.stderr = None

    def endCapture(self):
        captured = sys.stdout.getvalue()
        # end capture
        if self.stdout is not None:
            sys.stdout = self.stdout
            self.stdout = None
        if self.stderr is not None:
            sys.stderr = self.stderr
            self.stderr = None
        return captured

    def test_init(self):
        self.beginCapture()
        assert self.app.main(['assnet_test', 'init']) in (0, None)
        output = self.endCapture()
        assert output.strip() == "assnet working directory created."

        self.beginCapture()
        assert self.app.main(['assnet_test', 'tree']) in (0, None)
        output = self.endCapture()
        assert re.match(re.escape(r'-/') + r'\s+' + re.escape(r'all(irl-)'), output, re.S)
        assert re.match(".+" + re.escape(r'|-.assnet/') + r'\s+' + re.escape(r'all(----)'), output, re.S)

    def test_findRoot(self):
        self.beginCapture()
        assert self.app.main(['assnet_test', 'init']) in (0, None)
        self.endCapture()

        subdir = os.path.join(self.root, "penguins")
        os.mkdir(subdir)
        subapp = CLI(subdir)
        assert subapp.main(['assnet_test', 'tree']) in (0, None)

    def test_genKey(self):
        self.beginCapture()
        assert self.app.main(['assnet_test', 'init']) in (0, None)
        self.endCapture()

        storage = Storage.lookup(self.root)
        user = User(storage, 'penguin')
        user.realname = 'Penguin'
        user.password = 'monkey1'
        user.save()

        self.beginCapture()
        assert self.app.main(['assnet_test', 'contacts', 'genkey', 'penguin']) in (0, None)
        output = self.endCapture()
        assert 'Key of user penguin set' in output
