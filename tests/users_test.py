from ass2m.storage import Storage
from ass2m.users import User
from unittest import TestCase
from tempfile import mkdtemp
import shutil


class UsersTest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='ass2m_test_root')
        self.storage = Storage.create(self.root)

    def tearDown(self):
        if self.root:
            shutil.rmtree(self.root)

    def test_password(self):
        u = User(self.storage, 'penguin')
        assert not u.is_valid_password('hello')
        self.assertRaises(AssertionError, u.is_valid_password, None)
        self.assertRaises(AssertionError, u.is_valid_password, False)
        assert not u.is_valid_password('')

        u.password = 'hello'
        assert u.is_valid_password('hello')
        assert not u.is_valid_password('HELLO')
        assert not u.is_valid_password('')

        u.save()
        assert u.password is True
        self.assertRaises(AssertionError, u.is_valid_password, True)
        assert u.is_valid_password('hello')
        assert not u.is_valid_password('HELLO')
        assert not u.is_valid_password('')

        u = User(self.storage, 'penguin')
        u.read()
        assert u.password is True
        assert u.is_valid_password('hello')
        assert not u.is_valid_password('HELLO')
        assert not u.is_valid_password('')

        # Set the password to the same value.
        # If the salts and hashed passwords are the same, either our hashing
        # algorithm is weak or it's the end of the word.
        password1 = u.data['auth']['password']
        salt1 = u.data['auth']['salt']
        u.password = 'hello'
        u.save()
        password2 = u.data['auth']['password']
        salt2 = u.data['auth']['salt']
        assert password1 != password2
        assert salt1 != salt2

    def test_key(self):
        u1 = User(self.storage, 'penguin')
        u1.read()
        assert u1.key is None
        u1.gen_key()
        u1.save()

        u2 = User(self.storage, 'penguin')
        u2.read()
        assert len(u2.key)
        u2.gen_key()
        assert u2.key != u1.key
