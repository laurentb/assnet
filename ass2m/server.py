# -*- coding: utf-8 -*-

# Copyright(C) 2011  Romain Bignon, Laurent Bachelier
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.


import os
import posixpath
import re
from binascii import hexlify
from mako.lookup import TemplateLookup
from paste import httpserver
from paste.auth.cookie import AuthCookieSigner, new_secret
from webob import Request, Response
from webob.exc import HTTPFound, HTTPNotFound, HTTPForbidden
from paste.url import URL
import urlparse

from ass2m import Ass2m
from .users import Anonymous
from .routes import Router

class Context(object):
    SANITIZE_REGEXP = re.compile(r'/[%s+r]+/|\\+' % re.escape(r'/.'))

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
        path = self.req.path_info
        # remove the trailing "/" server-side, and other nice stuff
        path = self.SANITIZE_REGEXP.sub('/', path)
        path = posixpath.normpath(path)
        if path in ('.', '/'):
            path = ''

        if self.ass2m.root:
            f = self.ass2m.storage.get_file(path)
        else:
            f = None

        if f and f.isfile():
            self.object_type = "file"
        elif f and f.isdir():
            self.object_type = "directory"
        else:
            self.object_type = None

        query_vars = self.req.str_GET.items()
        # Path of the file relative to the Ass2m root
        self.path = path
        # Absolute path of the file on the system
        self.file = f
        # URL after Ass2m web application base URL
        self.relurl = URL(path, query_vars)
        # Complete URL
        self.url = URL(urlparse.urlparse(self.req.application_url).path + path, query_vars)
        # Root application URL (for links to special actions)
        self.root_url = URL(urlparse.urlparse(self.req.application_url).path)

    def _init_routing(self):
        router = Router()
        router.set_default_view(None, "html")
        router.set_default_view("download", "raw")
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
                         output_encoding='utf-8', input_encoding='utf-8',
                         default_filters=['decode.utf8'])

    def _init_default_response(self):
        # defaults, may be changed later on
        self.res.status = 200
        self.res.headers['Content-Type'] = 'text/html; charset=UTF-8'

    def _init_template_vars(self):
        self.template_vars = {
            'ass2m_version': Ass2m.VERSION,
            'path': self.path or "/",
            'url': self.url,
            'root_url': self.root_url,
            'global': dict(),
        }

    def render(self, template):
        return self.lookup.get_template(template).render(**self.template_vars)

    def respond(self):
        return self.res(self._environ, self._start_response)

    def iter_files(self):
        if self.object_type == "directory":
            for f in self.file.iter_children():
                if self.user.has_perms(f, f.PERM_LIST):
                    yield f


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
        ctx.template_vars["user"] = ctx.user if ctx.user.exists else None


        # actions not related to a file or directory
        action = router.match(None, ctx.req)
        if action is not None:
            return action(ctx).answer()

        # check perms
        f = ctx.file
        if not ctx.user.has_perms(f, f.PERM_READ):
            ctx.res = HTTPForbidden()
            return

        # normalize paths
        if f.file_exists():
            goodpath = ctx.path if len(ctx.path) else "/"
            if f.isdir() and goodpath[-1] != "/":
                # there should be a trailing slash in the client URL
                # for directories but not for files
                goodpath += "/"
            if ctx.req.path_info != goodpath:
                goodlocation = URL(ctx.req.application_url + goodpath, vars=ctx.url.vars)
                ctx.res = HTTPFound(location=goodlocation.href)
                return

        # no object type means no real file exists
        if ctx.object_type is None:
            ctx.res = HTTPNotFound('File not found')
            return

        # find out current action/view and available views
        ctx.template_vars["action"], ctx.template_vars["view"] = \
            router.resolve(ctx.object_type, ctx.req, f.view)
        ctx.template_vars["available_views"] = \
            sorted(router.available_views(ctx.object_type, ctx.template_vars["action"]))
        # find the action to forward the request to
        action = router.match(ctx.object_type, ctx.req, f.view)
        if action is not None:
            return action(ctx).answer()

        # action/view not found
        ctx.res = HTTPNotFound('No route found')

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

