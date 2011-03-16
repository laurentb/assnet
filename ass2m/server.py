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
import urlparse

from ass2m import Ass2m
from .users import Anonymous
from .routes import Router

class Context(object):
    def __init__(self, environ, start_response):
        self._init_routing()

        self.ass2m = Ass2m(environ.get("ASS2M_ROOT"), router=self.router)
        self._environ = environ
        self._start_response = start_response
        self.req = Request(environ)
        self.res = Response()
        self.user = Anonymous()

        self._init_paths()
        self._init_cookie_secret()
        self._init_templates()
        self._init_default_response()
        self._init_template_vars()

    def _init_paths(self):
        webpath = self.req.path_info
        # remove the trailing "/" server-side, and other nice stuff
        webpath = os.path.normpath(webpath)
        if webpath == ".":
            webpath = "/"

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
        if not self.ass2m.storage:
            return

        config = self.ass2m.storage.get_config()
        self.cookie_secret = config.data["web"].get("cookie_secret")
        if self.cookie_secret is None:
            self.cookie_secret = hexlify(new_secret())
            config.data["web"]["cookie_secret"] = self.cookie_secret
            config.save()


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

    def _init_template_vars(self):
        self.template_vars = {
            'ass2m_version': Ass2m.VERSION,
            'webpath': self.webpath.decode('utf-8'),
            'global': dict(),
        }

    def render(self, template):
        return self.lookup.get_template(template).render(**self.template_vars)

    def respond(self):
        return self.res(self._environ, self._start_response)


class Action(object):
    def __init__(self, ctx):
        self.ctx = ctx


    def answer(self):
        raise NotImplementedError()


class HTTPNormalizedPath(HTTPFound):
    """
    Like HTTPFound but keeps the QUERY_STRING.
    """

    def __call__(self, environ, start_response):
        req = Request(environ)
        url = self.location
        if req.environ.get('QUERY_STRING'):
            url += '?' + req.environ['QUERY_STRING']
        self.location = urlparse.urljoin(req.path_url, url)
        return super(HTTPNormalizedPath, self).__call__(
            environ, start_response)


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
        f = self.ctx.ass2m.storage.get_file(ctx.webpath)
        if not self.ctx.user.has_perms(f, f.PERM_READ):
            self.ctx.res = HTTPForbidden()
            return

        # normalize paths
        if os.path.exists(ctx.realpath):
            goodpath = ctx.webpath
            if os.path.isdir(ctx.realpath) and goodpath[-1] != "/":
                # there should be a trailing slash in the client URL
                # for directories but not for files
                goodpath += "/"
            if self.ctx.req.path_info != goodpath:
                self.ctx.res = HTTPNormalizedPath(location=goodpath)
                return

        # find the action to forward the request to
        if os.path.isfile(ctx.realpath):
            object_type = "file"
        elif os.path.isdir(ctx.realpath):
            object_type = "directory"
        else:
            self.ctx.res = HTTPNotFound('File not found')
            return

        ctx.template_vars["action"], ctx.template_vars["view"] = \
            router.resolve(object_type, ctx.req, f.view)
        ctx.template_vars["views"] = \
            sorted(router.available_views(object_type, ctx.template_vars["action"]))
        action = router.match(object_type, ctx.req, f.view)
        if action is not None:
            return action(ctx).answer()

        # action/view not found
        self.ctx.res = HTTPNotFound('No route found')


    def error_notworkingdir(self):
        self.ctx.res.status = 500
        if self.ctx._environ.has_key('ASS2M_ROOT'):
            self.ctx.template_vars['root'] = self.ctx._environ['ASS2M_ROOT']
            self.ctx.res.body = self.ctx.render('error_notworkingdir.html')
        else:
            self.ctx.res.body = self.ctx.render('error_norootpath.html')


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
            environ.setdefault("ASS2M_ROOT", self.root)
        ctx = Context(environ, start_response)
        dispatcher = Dispatcher(ctx)
        dispatcher.answer()
        return ctx.respond()

