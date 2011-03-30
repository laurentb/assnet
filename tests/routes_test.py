from ass2m.routes import View, Router
from unittest import TestCase

def fn1():
    pass

def fn2():
    pass

class FakeFile(object):
    def __init__(self, name, object_type, view = None):
        self.name = name
        self.object_type = object_type
        self.view = view

    def get_object_type(self):
        return self.object_type

class RoutesTest(TestCase):
    def test_actions(self):
        router = Router()
        router.register_action('login', fn1)
        router.register_action('logout', fn2)

        assert router.find_action(None) is None
        assert router.find_action('login') is fn1
        assert router.find_action('logout') is fn2
        assert router.find_action('fly') is None

    def test_objectTypeValidation(self):
        router = Router()
        router.register_view(View(object_type='file', name='json'), fn1)
        router.register_view(View(object_type='directory', name='json'), fn2)
        router.register_view(View(object_type=None, name='archive'), fn1)
        router.register_view(View(object_type='directory', name='gallery'), fn1)

        # same view, different action for a different object type
        assert router.find_view(FakeFile(name='penguin.txt', object_type='file'), 'json')[1] is fn1
        assert router.find_view(FakeFile(name='penguin', object_type='directory'), 'json')[1] is fn2
        # accepts any object type
        assert router.find_view(FakeFile(name='penguin.txt', object_type='file'), 'archive')[1] is fn1
        assert router.find_view(FakeFile(name='penguin', object_type='directory'), 'archive')[1] is fn1
        # no such view
        assert router.find_view(FakeFile(name='penguin.txt', object_type='file'), 'raw')[1] is None
        # no such view for this type
        assert router.find_view(FakeFile(name='penguin.txt', object_type='file'), 'gallery')[1] is None
        assert router.find_view(FakeFile(name='penguin', object_type='directory'), 'gallery')[1] is fn1

    def test_priorityForDefaults(self):
        router = Router()
        router.register_view(View(object_type='file', name='raw'), fn1, 10)
        router.register_view(View(object_type='file', name='json'), fn2, 1)
        router.register_view(View(object_type='directory', name='json'), fn2, 1)
        router.register_view(View(object_type='directory', name='list'), fn1, 10)

        view, call = router.find_view(FakeFile(name='penguin.txt', object_type='file'))
        assert view.name == 'raw'
        assert call == fn1
        view, call = router.find_view(FakeFile(name='penguin.txt', object_type='file'), 'json')
        assert view.name == 'json'
        assert call == fn2
        view, call = router.find_view(FakeFile(name='penguin', object_type='directory'))
        assert view.name == 'list'
        assert call == fn1
        view, call = router.find_view(FakeFile(name='penguin', object_type='directory'), 'json')
        assert view.name == 'json'
        assert call == fn2

    def test_viewsList(self):
        router = Router()
        router.register_view(View(object_type='file', name='raw'), None)
        router.register_view(View(object_type='file', name='yaml', public=False), None)
        router.register_view(View(object_type=None, name='json'), None)
        router.register_view(View(object_type='directory', name='list'), None)

        assert sorted([r.name for r in router.get_available_views(FakeFile(name='penguin.txt', object_type='file')) if r.public]) == ['json', 'raw']
        assert sorted([r.name for r in router.get_available_views(FakeFile(name='penguin.txt', object_type='file'))]) == ['json', 'raw', 'yaml']
        assert sorted([r.name for r in router.get_available_views(FakeFile(name='penguin', object_type='directory'))]) == ['json', 'list']

    def test_fileView(self):
        router = Router()
        router.register_view(View(object_type='file', name='raw'), fn1, 10)
        router.register_view(View(object_type='file', name='json'), fn2, 1)

        view, call = router.find_view(FakeFile(name='penguin.txt', object_type='file', view='json'))
        assert view.name == 'json'
        assert call == fn2
        view, call = router.find_view(FakeFile(name='penguin.txt', object_type='file', view='json'), 'raw')
        assert view.name == 'raw'
        assert call == fn1
        view, call = router.find_view(FakeFile(name='penguin.txt', object_type='file', view='doesnotexist'))
        assert view is None
        assert call is None

    def test_verboseName(self):
        assert View(object_type='directory', name='list').verbose_name == 'List'
        assert View(object_type='directory', name='this_is_a_list').verbose_name == 'This Is A List'
        assert View(object_type='directory', name='list', verbose_name='Detailed list').verbose_name == 'Detailed list'
