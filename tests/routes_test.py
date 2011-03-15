from ass2m.routes import Route, Router
from webtest import TestApp
from webob import Request, Response
from unittest import TestCase

class RoutesTest(TestCase):
    def setUp(self):
        router = Router()
        def app(environ, start_response):
            req = Request(environ)
            res = Response(content_type='text/plain')
            res.body = repr(router.match(environ["ASS2M_OBJECT_TYPE"], req))
            return res(environ, start_response)

        self.app = TestApp(app)
        self.router = router


    def test_addAndMatch(self):
        def fn1():
            pass

        self.router.connect(Route(object_type="file", action="list", view="html"), fn1)

        extra_environ = {"ASS2M_OBJECT_TYPE": "file"}
        res = self.app.get("/?action=list&view=html", extra_environ=extra_environ)
        assert repr(fn1) == res.body
        res = self.app.get("/?action=plop&view=html", extra_environ=extra_environ)
        assert "None" == res.body


    def test_getOrPost(self):
        def fn1():
            pass

        def fn2():
            pass

        self.router.connect(Route(object_type="file", action="list", view="html", method="GET"), fn1)
        self.router.connect(Route(object_type="file", action="list", view="html", method="POST"), fn2)

        extra_environ = {"ASS2M_OBJECT_TYPE": "file"}
        res = self.app.get("/?action=list&view=html", extra_environ=extra_environ)
        assert repr(fn1) == res.body
        res = self.app.post("/?action=list&view=html", extra_environ=extra_environ)
        assert repr(fn2) == res.body


    def test_catchAllView(self):
        def fn1():
            pass

        def fn2():
            pass

        self.router.connect(Route(object_type="file", action="list", view=None), fn1)
        self.router.connect(Route(object_type="file", action="list", view="html"), fn2)

        extra_environ = {"ASS2M_OBJECT_TYPE": "file"}
        res = self.app.get("/?action=list&view=json", extra_environ=extra_environ)
        assert repr(fn1) == res.body
        res = self.app.get("/?action=list&view=html", extra_environ=extra_environ)
        assert repr(fn2) == res.body


    def test_catchAllViewAndPrecision(self):
        def fn1():
            pass

        def fn2():
            pass

        self.router.connect(Route(object_type="file", action="list", view="html"), fn1)
        self.router.connect(Route(object_type="file", action="list", view=None), fn2)

        extra_environ = {"ASS2M_OBJECT_TYPE": "file"}
        res = self.app.get("/?action=list&view=json", extra_environ=extra_environ)
        assert repr(fn2) == res.body
        res = self.app.get("/?action=list&view=html", extra_environ=extra_environ)
        assert repr(fn1) == res.body


    def test_setDefaultAction(self):
        def fn1():
            pass

        def fn2():
            pass

        self.router.connect(Route(object_type="directory", action="list", view="html"), fn1)
        self.router.set_default_action("directory", "list")

        extra_environ = {"ASS2M_OBJECT_TYPE": "directory"}
        res = self.app.get("/", extra_environ=extra_environ)
        assert "None" == res.body
        res = self.app.get("/?view=html", extra_environ=extra_environ)
        assert repr(fn1) == res.body
        res = self.app.get("/?action=tar&view=html", extra_environ=extra_environ)
        assert "None" == res.body

        extra_environ = {"ASS2M_OBJECT_TYPE": "file"}
        res = self.app.get("/?view=html", extra_environ=extra_environ)
        assert "None" == res.body


    def test_setDefaultActionAndView(self):
        def fn1():
            pass

        def fn2():
            pass

        def fn3():
            pass

        self.router.connect(Route(object_type="directory", action="list", view="html"), fn1)
        self.router.connect(Route(object_type="directory", action="list", view="json"), fn2)
        self.router.connect(Route(object_type="directory", action="tree", view="json"), fn3)
        self.router.set_default_action("directory", "list")
        self.router.set_default_view("list", "html")
        self.router.set_default_view("tree", "json")
        extra_environ = {"ASS2M_OBJECT_TYPE": "directory"}

        res = self.app.get("/", extra_environ=extra_environ)
        assert repr(fn1) == res.body
        res = self.app.get("/?view=json", extra_environ=extra_environ)
        assert repr(fn2) == res.body
        res = self.app.get("/?action=tree", extra_environ=extra_environ)
        assert repr(fn3) == res.body


    def test_manualPrecision(self):
        def fn1():
            pass

        def fn2():
            pass

        self.router.connect(Route(object_type="file", action="list", view="html"), fn1)
        route = Route(object_type="file", action="list", view=None)
        route.precision = 42
        self.router.connect(route, fn2)

        extra_environ = {"ASS2M_OBJECT_TYPE": "file"}
        res = self.app.get("/?action=list&view=json", extra_environ=extra_environ)
        assert repr(fn2) == res.body
        res = self.app.get("/?action=list&view=html", extra_environ=extra_environ)
        assert repr(fn2) == res.body


    def test_viewsList(self):
        self.router.connect(Route(object_type="directory", action="list", view="html"), None)
        self.router.connect(Route(object_type="directory", action="list", view="json"), None)
        self.router.connect(Route(object_type="directory", action="tree", view="xml"), None)
        self.router.connect(Route(object_type="file", action="list", view="yaml"), None)
        self.router.connect(Route(object_type="directory", action="list", view=None), None)

        assert sorted(self.router.available_views("directory", "list")) == ["html", "json"]
        assert sorted(self.router.available_views("directory", "tar")) == []
        assert sorted(self.router.available_views("file", "list")) == ["yaml"]
