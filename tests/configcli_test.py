from unittest import TestCase
from ass2m.cli import CLI
from ass2m.storage import Storage
from tempfile import mkdtemp
import os
import shutil
import sys
from StringIO import StringIO

class ConfigCLITest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='ass2m_test_root')
        Storage.create(self.root)
        self.app = CLI(self.root)
        os.mkdir(os.path.join(self.root, 'penguins'))
        with open(os.path.join(self.root, 'penguins', 'gentoo'), 'w') as f:
            f.write('HELLO')

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

    def test_resolve(self):
        for p in (os.path.join(self.root, 'penguins'), os.path.join(self.root, 'penguins'+os.path.sep)):
            self.beginCapture()
            assert self.app.main(['ass2m_test', 'config', 'resolve', p]) in (0, None)
            output = self.endCapture()
            assert output.startswith('/penguins => ')
            assert output.strip().endswith('/7fe0243160cdd4fdb87ab2ce1ecf9fef501cd1a5')

        self.beginCapture()
        assert self.app.main(['ass2m_test', 'config', 'resolve', os.path.join(self.root, 'penguins', 'gentoo')]) in (0, None)
        output = self.endCapture()
        assert output.startswith('/penguins/gentoo => ')
        assert output.strip().endswith('/090ec30f855081df160d60cbfe635c399b5ff523')

        self.beginCapture()
        assert self.app.main(['ass2m_test', 'config', 'resolve', self.root]) in (0, None)
        output = self.endCapture()
        assert output.startswith(' => ')
        assert output.strip().endswith('/da39a3ee5e6b4b0d3255bfef95601890afd80709')

    def test_configList(self):
        self.beginCapture()
        assert self.app.main(['ass2m_test', 'config', 'global', 'list']) in (0, None)
        output = self.endCapture()
        assert len(output) == 0
