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
        assert "<function fn1" in res.body

        res = self.app.get("/?action=plop&view=html", extra_environ=extra_environ)
        assert "False" == res.body

    def test_getOrPost(self):
        def fn1():
            pass

        def fn2():
            pass

        self.router.connect(Route(object_type="file", action="list", view="html", method="GET"), fn1)
        self.router.connect(Route(object_type="file", action="list", view="html", method="POST"), fn2)
        extra_environ = {"ASS2M_OBJECT_TYPE": "file"}

        res = self.app.get("/?action=list&view=html", extra_environ=extra_environ)
        assert "<function fn1" in res.body
        res = self.app.post("/?action=list&view=html", extra_environ=extra_environ)
        assert "<function fn2" in res.body

    def test_catchAllView(self):
        def fn1():
            pass

        def fn2():
            pass

        self.router.connect(Route(object_type="file", action="list", view=None), fn1)
        self.router.connect(Route(object_type="file", action="list", view="html"), fn2)
        extra_environ = {"ASS2M_OBJECT_TYPE": "file"}

        res = self.app.get("/?action=list&view=json", extra_environ=extra_environ)
        assert "<function fn1" in res.body
        res = self.app.get("/?action=list&view=html", extra_environ=extra_environ)
        assert "<function fn2" in res.body

    def test_catchAllViewAndPriority(self):
        def fn1():
            pass

        def fn2():
            pass

        self.router.connect(Route(object_type="file", action="list", view="html"), fn1)
        self.router.connect(Route(object_type="file", action="list", view=None), fn2)
        extra_environ = {"ASS2M_OBJECT_TYPE": "file"}

        res = self.app.get("/?action=list&view=json", extra_environ=extra_environ)
        assert "<function fn2" in res.body
        res = self.app.get("/?action=list&view=html", extra_environ=extra_environ)
        assert "<function fn2" in res.body

