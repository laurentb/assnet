from __future__ import with_statement

from ass2m.storage import Storage
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
        storage = Storage.create(self.root)
        server = Server(self.root)
        self.app = TestApp(server.process)

        user = User(storage, 'penguin')
        user.realname = 'Penguin'
        user.password = 'monkey1'
        user.save()
        user = User(storage, 'platypus')
        user.realname = 'Platypus'
        user.password = 'passw0rd'
        user.save()

        event_text = """Reunion
---

Reunion of the penguins

Date:
2001-02-03 13:37

Place:
Somewhere

Attendees:
[ ] penguin (Penguin)
[x] platypus (Platypus)
-- 0 confirmed, 0 waiting, 0 declined

        """
        with open(os.path.join(self.root, 'event1.txt'), 'w') as f:
            f.write(event_text)

        f = storage.get_file('/event1.txt')
        f.view = 'event'
        f.perms['u.penguin'] = f.PERM_READ|f.PERM_WRITE
        f.save()

    def tearDown(self):
        if self.root:
            shutil.rmtree(self.root)

    def test_viewEvent(self):
        res = self.app.get('/event1.txt', status=200)
        assert '<h3>Place</h3>' in res.body
        assert 'Your current status' not in res.body
        assert 'Accept</button>' not in res.body
        assert 'Decline</button>' not in res.body

        res = self.app.get('/?action=login', status=200)
        form = res.form
        form['login[username]'] = 'penguin'
        form['login[password]'] = 'monkey1'
        res = form.submit(status=302)
        res = res.follow(status=200)

        res = self.app.get('/event1.txt', status=200)
        assert '<h3>Place</h3>' in res.body
        assert '<strong>waiting</strong>' in res.body
        assert 'Confirm</button>' in res.body
        assert 'Decline</button>' in res.body

        # decline then accept ('REST' style)
        res = self.app.delete('/event1.txt', status=200)
        assert '<h3>Place</h3>' in res.body
        assert '<strong>declined</strong>' in res.body
        assert 'Confirm</button>' in res.body
        assert 'Decline</button>' not in res.body

        res = self.app.put('/event1.txt', status=200)
        assert '<h3>Place</h3>' in res.body
        assert '<strong>confirmed</strong>' in res.body
        assert 'Confirm</button>' not in res.body
        assert 'Decline</button>' in res.body

        # same but for browsers
        res = self.app.post('/event1.txt', {'_method': 'DELETE'}, status=200)
        assert '<h3>Place</h3>' in res.body
        assert '<strong>declined</strong>' in res.body
        assert 'Confirm</button>' in res.body
        assert 'Decline</button>' not in res.body

        res = self.app.put('/event1.txt', {'_method': 'PUT'}, status=200)
        assert '<h3>Place</h3>' in res.body
        assert '<strong>confirmed</strong>' in res.body
        assert 'Confirm</button>' not in res.body
        assert 'Decline</button>' in res.body
