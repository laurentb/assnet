from assnet.storage import Storage
from assnet.server import Server

from unittest import TestCase
from webtest import TestApp

from tempfile import mkdtemp
from PIL import Image
from StringIO import StringIO
import os
import shutil


class GalleryTest(TestCase):
    def setUp(self):
        self.root = mkdtemp(prefix='assnet_test_root')
        self.storage = Storage.create(self.root)
        server = Server(self.root)
        self.app = TestApp(server)
        os.mkdir(os.path.join(self.root, 'images'))
        os.mkdir(os.path.join(self.root, 'images', 'nothing'))

        with open(os.path.join(self.root, 'DESCRIPTION'), 'w') as f:
            f.write('This is my awesome gallery!')

        with open(os.path.join(self.root, 'images', 'notanimage.txt'), 'w') as f:
            f.write('HELLO')

        with open(os.path.join(self.root, 'images', 'image1.jpg'), 'wb') as f:
            img = Image.new('RGB', (1337, 1337), (255, 0, 0))
            img.save(f, 'jpeg')

        with open(os.path.join(self.root, 'images', 'image2.jpg'), 'wb') as f:
            img = Image.new('RGB', (1337, 1337), (0, 255, 0))
            img.save(f, 'jpeg')

    def tearDown(self):
        if self.root:
            shutil.rmtree(self.root)

    def test_listAndDefaultView(self):
        # default view is the medialist
        res1 = self.app.get('/images/')

        # change it to list
        f = self.storage.get_file('/images')
        f.view = 'list'
        f.save()

        res = self.app.get('/images/')
        assert '<title>Index of /images/</title>' in res.body
        assert '<img' not in res.body
        assert 'nothing' in res.body

        # force medialist
        res2 = self.app.get('/images/?view=medialist')

        for res in (res1, res2):
            assert '<title>Index of /images/</title>' in res.body
            assert '<img' in res.body
            assert 'nothing' in res.body

    def test_getThumbnail(self):
        res = self.app.get('/images/image1.jpg?view=thumbnail')
        img = Image.open(StringIO(res.body))
        img.verify()
        img = Image.open(StringIO(res.body))
        assert img.size[0] < 1000
        assert img.size[1] < 1000

        res = self.app.get('/images/image1.jpg?view=thumbnail&thumb_size=42')
        img = Image.open(StringIO(res.body))
        assert img.size[0] == 42
        assert img.size[1] == 42

        res = self.app.get('/images/notanimage.txt?view=thumbnail', status=404)

    def test_getRaw(self):
        # check we get the full image and not the thumbnail
        res = self.app.get('/images/image1.jpg')
        img = Image.open(StringIO(res.body))
        img.verify()
        img = Image.open(StringIO(res.body))
        assert img.size[0] == 1337
        assert img.size[1] == 1337
