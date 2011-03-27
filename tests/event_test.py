from __future__ import with_statement

from ass2m.ass2m import Ass2m
from ass2m.server import Server
from ass2m.users import User

from unittest import TestCase
from webtest import TestApp

from tempfile import mkdtemp
import os
import shutil

class EventTest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='ass2m_test_root')
        ass2m = Ass2m(self.root)
        ass2m.create(self.root)
        server = Server(self.root)
        self.app = TestApp(server.process)

        user = User(ass2m.storage, 'penguin')
        user.realname = 'Penguin'
        user.save()

        event_text = """Reunion
---

Reunion of the penguins

Date:
2001-02-03 13:37

Place:
Somewhere

Attendees:
[x] penguin (Penguin)
-- 1 confirmed, 0 waiting, 0 declined

        """
        with open(os.path.join(self.root, 'event1.txt'), 'w') as f:
            f.write(event_text)

        f = ass2m.storage.get_file('/event1.txt')
        f.view = 'event'
        f.save()

    def tearDown(self):
        if self.root:
            shutil.rmtree(self.root)

    def test_viewEvent(self):
        res = self.app.get('/event1.txt', status=200)
        assert '<h3>Place</h3>' in res.body
