from unittest import TestCase
from ass2m.cli import CLI
from ass2m.storage import Storage
from ass2m.users import User
from tempfile import mkdtemp
import os
import shutil
import sys
from StringIO import StringIO


class ConfigCLITest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='ass2m_test_root')
        storage = Storage.create(self.root)
        self.app = CLI(self.root)

        os.mkdir(os.path.join(self.root, 'penguins'))
        with open(os.path.join(self.root, 'penguins', 'gentoo'), 'w') as f:
            f.write('HELLO')

        user = User(storage, 'penguin')
        user.realname = 'Penguin'
        user.password = 'monkey1'
        user.key = 'fabf37d746da8a45df63489f642b3813'
        user.save()

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

    def test_resolve(self):
        for p in (os.path.join(self.root, 'penguins'), os.path.join(self.root, 'penguins' + os.path.sep)):
            self.beginCapture()
            assert self.app.main(['ass2m_test', 'config', '-f', p, 'resolve']) in (0, None)
            output = self.endCapture()
            assert output.startswith('/penguins => ')
            assert output.strip().endswith('/7fe0243160cdd4fdb87ab2ce1ecf9fef501cd1a5')

        self.beginCapture()
        assert self.app.main(['ass2m_test', 'config', '-f', os.path.join(self.root, 'penguins', 'gentoo'), 'resolve']) in (0, None)
        output = self.endCapture()
        assert output.startswith('/penguins/gentoo => ')
        assert output.strip().endswith('/090ec30f855081df160d60cbfe635c399b5ff523')

        self.beginCapture()
        assert self.app.main(['ass2m_test', 'config', '-f', self.root, 'resolve']) in (0, None)
        output = self.endCapture()
        assert output.startswith(' => ')
        assert output.strip().endswith('/da39a3ee5e6b4b0d3255bfef95601890afd80709')

        self.beginCapture()
        assert self.app.main(['ass2m_test', 'config', '-g', 'resolve']) in (0, None)
        output = self.endCapture()
        assert output.startswith('<global> => ')
        assert output.strip().endswith('/config')

        self.beginCapture()
        assert self.app.main(['ass2m_test', 'config', '-u', 'penguin', 'resolve']) in (0, None)
        output = self.endCapture()
        assert output.startswith('penguin => ')
        assert output.strip().endswith('/users/penguin')

    def test_configList(self):
        self.beginCapture()
        assert self.app.main(['ass2m_test', 'config', '-g', 'list']) in (0, None)
        output = self.endCapture()
        assert 'storage.version' in output

        self.beginCapture()
        assert self.app.main(['ass2m_test', 'config', '-f', self.root, 'list']) in (0, None)
        output = self.endCapture()
        assert len(output)  # it has the default perms

        self.beginCapture()
        assert self.app.main(['ass2m_test', 'config', '-u', 'penguin', 'list']) in (0, None)
        output = self.endCapture()  # no ValueError
        assert len(output)

    def test_filterList(self):
        self.beginCapture()
        assert self.app.main(['ass2m_test', 'config', '-u', 'penguin', 'list']) in (0, None)
        output = self.endCapture()
        assert len(output)
        output.split('\n').index('info.realname=Penguin')  # no ValueError

        self.beginCapture()
        assert self.app.main(['ass2m_test', 'config', '-u', 'penguin', 'list', 'auth']) in (0, None)
        output = self.endCapture()
        assert len(output)
        self.assertRaises(ValueError, output.split('\n').index, 'info.realname=Penguin')

    def test_getAndSet(self):
        self.beginCapture()
        assert self.app.main(['ass2m_test', 'config', '-g', 'list']) in (0, None)
        output = self.endCapture()
        assert 'lol.cat' not in output

        self.beginCapture(True)
        assert self.app.main(['ass2m_test', 'config', '-g', 'get', 'lol.cat']) == 2
        output = self.endCapture()
        assert output.strip() == 'Error: lol.cat is undefined.'
        self.beginCapture()
        assert self.app.main(['ass2m_test', 'config', '-g', 'set', 'lol.cat', '42']) in (0, None)
        output = self.endCapture()
        assert len(output) == 0

        self.beginCapture()
        assert self.app.main(['ass2m_test', 'config', '-g', 'get', 'lol.cat']) in (0, None)
        output = self.endCapture()
        assert output.strip() == '42'

        self.beginCapture()
        assert self.app.main(['ass2m_test', 'config', '-g', 'list']) in (0, None)
        output = self.endCapture()
        assert 'lol.cat=42' in output
