from unittest import TestCase
from ass2m.cli import CLI
from tempfile import mkdtemp
import shutil
import sys
import re
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
