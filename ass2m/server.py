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
from webob.exc import HTTPFound, HTTPNotFound, HTTPForbidden

from ass2m import Ass2m
from .users import Anonymous
from .routes import Router

class Context(object):
    def __init__(self, environ, start_response):
        self._init_routing()

        self.ass2m = Ass2m(environ.get("ASS2M_ROOT"), ctx=self)
        self._environ = environ
        self._start_response = start_response
        self.req = Request(environ)
        self.res = Response()
        self.user = Anonymous()

        self._init_paths()
        self._init_cookie_secret()
        self._init_templates()
        self._init_default_response()

    def _init_paths(self):
        webpath = self.req.path_info
        # remove the trailing "/" server-side, and other nice stuff
        webpath = os.path.normpath(webpath)

        if self.ass2m.root:
            realpath = os.path.realpath(os.path.join(self.ass2m.root, webpath[1:]))
        else:
            realpath = None

        self.webpath = webpath
        self.realpath = realpath

    def _init_routing(self):
        router = Router()
        router.set_default_view(None, "html")
        router.set_default_action("file", "download")
        router.set_default_action("directory", "list")
        self.router = router


    def _init_cookie_secret(self):
        self.cookie_secret = self.ass2m.storage.config.setdefault("web", {}).get("cookie_secret")
        if self.cookie_secret is None:
            self.cookie_secret = hexlify(new_secret())
            self.ass2m.storage.config["web"]["cookie_secret"] = self.cookie_secret
            self.ass2m.storage.save_config()


    def _init_templates(self):
        paths = [os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data')),
                 '/usr/share/ass2m',
                 '/usr/local/share/ass2m']
        self.lookup = TemplateLookup(directories=['%s/templates' % path for path in paths],
                                     collection_size=20,
                                     output_encoding='utf-8')

    def _init_default_response(self):
        # defaults, may be changed later on
        self.res.status = 200
        self.res.headers['Content-Type'] = 'text/html; charset=UTF-8'


    def wsgi_response(self):
        return self.res(self._environ, self._start_response)


class Action(object):
    def __init__(self, ctx):
        self.ctx = ctx


    def answer(self):
        raise NotImplementedError()


class Dispatcher(Action):
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
        action = router.match(None, ctx.req)
        if action is not None:
            return action(ctx).answer()

        # check perms
        f = self.ctx.ass2m.storage.get_file(ctx.realpath)
        if not self.ctx.user.has_perms(f, f.PERM_READ):
            self.ctx.res = HTTPForbidden()
            return self.ctx.wsgi_response()

        # normalize paths of directories
        if os.path.isdir(ctx.realpath):
            if self.ctx.req.path_info[-1] != '/':
                # there should be a trailing slash in the client URL
                self.ctx.res = HTTPFound(add_slash=True)
                return self.ctx.wsgi_response()

        # find the action to forward the request to
        if os.path.isfile(ctx.realpath):
            action = router.match("file", ctx.req)
        elif os.path.isdir(ctx.realpath):
            action = router.match("directory", ctx.req)
        else:
            action = None

        if action is not None:
            return action(ctx).answer()
        else:
            # Either file or action/view not found
            self.ctx.res = HTTPNotFound()
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
        dispatcher = Dispatcher(ctx)
        return dispatcher.answer()

