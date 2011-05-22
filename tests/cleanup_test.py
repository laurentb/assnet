from unittest import TestCase
from ass2m.cli import CLI
from ass2m.storage import Storage
from tempfile import mkdtemp
import shutil
import os
import sys
from StringIO import StringIO


class CleanupTest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='ass2m_test_root')
        self.storage = Storage.create(self.root)
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

    def test_simpleRun(self):
        self.beginCapture()
        assert self.app.main(['ass2m_test', 'cleanup']) in (0, None)
        output = self.endCapture()
        assert output.strip() == ''

        self.beginCapture()
        assert self.app.main(['ass2m_test', 'cleanup', '--gc']) in (0, None)
        output = self.endCapture()
        assert output.strip() == ''

    def test_invalidPaths(self):
        with open(os.path.join(self.storage.path, 'files', 'hello'), 'w') as f:
            f.write('')

        self.beginCapture()
        assert self.app.main(['ass2m_test', 'cleanup']) in (0, None)
        output = self.endCapture()
        assert output.strip() == 'files/hello has an invalid path: None.'

        self.beginCapture()
        assert self.app.main(['ass2m_test', 'cleanup', '--gc']) in (0, None)
        output = self.endCapture()
        assert output.strip() == 'files/hello has an invalid path: None.\nRemoved files/hello.'
        with open(os.path.join(self.storage.path, 'files', 'c93c3312483174a3170ebe7395612c404a0620d0'), 'w') as f:
            f.write('[info]\npath = /hello')

        self.beginCapture()
        assert self.app.main(['ass2m_test', 'cleanup']) in (0, None)
        output = self.endCapture()
        assert output.strip() == 'files/c93c3312483174a3170ebe7395612c404a0620d0 has an invalid path: /hello.'

        self.beginCapture()
        assert self.app.main(['ass2m_test', 'cleanup', '--gc']) in (0, None)
        output = self.endCapture()
        assert output.strip() == 'files/c93c3312483174a3170ebe7395612c404a0620d0 has an invalid path: /hello.\nRemoved files/c93c3312483174a3170ebe7395612c404a0620d0.'

    def test_oldStorageBug(self):
        with open(os.path.join(self.storage.path, 'files', '3be00feb429b32b7705b689475e3ab8bdf16733f'), 'w') as f:
            f.write('[info]\npath = /hello\nview = None')

        self.beginCapture()
        assert self.app.main(['ass2m_test', 'cleanup', '--gc']) in (0, None)
        output = self.endCapture()
        assert output.strip() == 'files/3be00feb429b32b7705b689475e3ab8bdf16733f: fixed empty view.'
