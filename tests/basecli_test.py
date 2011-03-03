from unittest import TestCase
from ass2m.cli import CLI
from tempfile import mkdtemp
import shutil

class BaseCLITest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='ass2m_test_root')
        self.app = CLI(self.root)

    def tearDown(self):
        if self.root:
            shutil.rmtree(self.root)

    def test_init(self):
        assert self.app.main(['ass2m_test', 'init']) in (0, None)

        assert self.app.main(['ass2m_test', 'tree']) in (0, None)
