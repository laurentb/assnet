# -*- coding: utf-8 -*-

# Copyright(C) 2011  Romain Bignon, Laurent Bachelier
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.


import os
from binascii import hexlify
from mako.lookup import TemplateLookup
from paste import httpserver
from paste.auth.cookie import AuthCookieSigner, new_secret
from webob import Request, Response
from webob import html_escape
from webob.exc import HTTPFound, HTTPNotFound, HTTPForbidden

from ass2m import Ass2m
from .users import Anonymous
from .routes import Router, Route

class Context(object):
    def __init__(self, environ, start_response):
        self.router = Router()
        self.ass2m = Ass2m(environ.get("ASS2M_ROOT", None), ctx=self)
        self._environ = environ
        self._start_response = start_response
        self.req = Request(environ)
        self.res = Response()
        self.user = Anonymous()

        self.cookie_secret = self.ass2m.storage.config.setdefault("web", {}).get("cookie_secret")
        if self.cookie_secret is None:
            self.cookie_secret = hexlify(new_secret())
            self.ass2m.storage.config["web"]["cookie_secret"] = self.cookie_secret
            self.ass2m.storage.save_config()

        paths = [os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data')),
                 '/usr/share/ass2m',
                 '/usr/local/share/ass2m']
        self.lookup = TemplateLookup(directories=['%s/templates' % path for path in paths],
                                     collection_size=20,
                                     output_encoding='utf-8')

        # defaults, may be changed later on
        self.res.status = 200
        self.res.headers['Content-Type'] = 'text/html; charset=UTF-8'

    def wsgi_response(self):
        return self.res(self._environ, self._start_response)


class Actions(object):
    def __init__(self, ctx):
        self.ctx = ctx
        self._register_routes()

    def _register_routes(self):
        pass


class DispatchActions(Actions):
    def _register_routes(self):
        router = self.ctx.router

        router.set_default_view(None, "html")
        router.set_default_action("file", "download")
        router.set_default_action("directory", "list")

        router.connect(
            Route(object_type = None, action="login"),
            self.login)
        router.connect(
            Route(object_type = None, action="login", method="POST"),
            self.login)


    def _authenticate(self):
        signer = AuthCookieSigner(secret=self.ctx.cookie_secret)
        cookie = self.ctx.req.str_cookies.get('ass2m_auth')
        user = cookie and signer.auth(cookie)
        if user:
            self.ctx.user = self.ctx.ass2m.storage.get_user(user)


    def answer(self):
        ctx = self.ctx
        router = ctx.router

        if not ctx.ass2m.storage:
            return self.error_notworkingdir()

        self._authenticate()

        # actions not related to a file or directory
        call = router.match(None, ctx.req)
        if call:
            return call()

        relpath = self.ctx.req.path_info
        fpath = os.path.join(self.ctx.ass2m.root, relpath[1:])

        # check perms
        f = self.ctx.ass2m.storage.get_file(relpath)
        if not self.ctx.user.has_perms(f, f.PERM_READ):
            self.ctx.res = HTTPForbidden()
            return self.ctx.wsgi_response()

        # normalize paths of directories
        if os.path.isdir(fpath):
            if self.ctx.req.path_info[-1] != '/':
                # there should be a trailing in the client URL "/"
                self.ctx.res = HTTPFound(add_slash=True)
                return self.ctx.wsgi_response()
            if relpath[-1] == '/':
                # remove the trailing "/" server-side
                relpath = os.path.dirname(relpath)

        # find the action to forward the request to
        if os.path.isfile(fpath):
            call = router.match("file", ctx.req)
        elif os.path.isdir(fpath):
            call = router.match("directory", ctx.req)
        else:
            call = False

        if call:
            return call(relpath, fpath)
        else:
            # Either file or action/view not found
            self.ctx.res = HTTPNotFound()
            return self.ctx.wsgi_response()


    def login(self):
        signer = AuthCookieSigner(secret=self.ctx.cookie_secret)
        form_user = self.ctx.req.str_POST.get('user')
        if form_user:
            # set cookie
            cookie = signer.sign(form_user)
            self.ctx.res.set_cookie('ass2m_auth', cookie)

            self.ctx.user = self.ctx.ass2m.storage.get_user(form_user)

        self.ctx.res.body = """<html><body>Current user: %s<br/>
                        <form method="post"><label>Username</label><input name="user" />
                        <input type="submit" /></form>
                        </body></html>""" % html_escape(str(self.ctx.user))

        return self.ctx.wsgi_response()


    def error_notworkingdir(self):
        self.ctx.res.status = 500
        if self.ctx._environ.has_key("ASS2M_ROOT"):
            self.ctx.res.body = self.ctx.lookup.get_template('error_notworkingdir.html'). \
                        render(root=self.ctx._environ["ASS2M_ROOT"])
        else:
            self.ctx.res.body = self.ctx.lookup.get_template('error_norootpath.html'). \
                        render()

        return self.ctx.wsgi_response()


class Server(object):
    def __init__(self, root=None):
        """
        The optional root parameter is used to force a root directory.
        If not present, the ASS2M_ROOT of environ (provided by the HTTP server)
        will be used.
        """
        self.root = root

    def bind(self, hostname, port):
        httpserver.serve(self.process, host=hostname, port=str(port))

    def process(self, environ, start_response):
        """
        WSGI interface
        """
        if self.root:
            environ["ASS2M_ROOT"] = self.root
        ctx = Context(environ, start_response)
        actions = DispatchActions(ctx)
        return actions.answer()

