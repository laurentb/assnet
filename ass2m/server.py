# -*- coding: utf-8 -*-

# Copyright (C) 2011 Romain Bignon, Laurent Bachelier
#
# This file is part of ass2m.
#
# ass2m is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ass2m is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with ass2m. If not, see <http://www.gnu.org/licenses/>.


import posixpath
import re
from binascii import hexlify
from paste import httpserver
from paste.auth.cookie import AuthCookieSigner, new_secret
from paste.fileapp import FileApp as PasteFileApp
from webob import Request, Response
from webob.exc import HTTPError, HTTPFound, HTTPNotFound, HTTPForbidden, \
        HTTPMethodNotAllowed, HTTPInternalServerError
from paste.url import URL
from paste.auth.basic import AuthBasicAuthenticator
from paste.httpheaders import REMOTE_USER, AUTH_TYPE
from datetime import timedelta
import urlparse
import json

from .butt import Butt
from .storage import Storage
from .template import build_lookup, build_vars
from .users import Anonymous
from .routes import Router
from .filters import quote_url, quote_path


__all__ = ['ViewAction', 'Action', 'Server', 'FileApp']


class Context(object):
    SANITIZE_REGEXP = re.compile(r'/[%s+r]+/|\\+|/+' % re.escape(r'/.'))

    def __init__(self, butt, environ, start_response):
        self.router = butt.router
        self.storage = Storage.lookup(environ.get("ASS2M_ROOT"))
        self._environ = environ
        self._start_response = start_response
        self.req = Request(environ)
        # fix script_name for weird configurations
        if 'SCRIPT_URL' in environ:
            script_path = quote_path(environ['SCRIPT_URL'])
            if self.req.path_info:
                level = len(self.req.path_info.split('/')) - 1
                environ['SCRIPT_NAME'] = '/'.join(script_path.split('/')[:-level]) + '/'
            else:
                environ['SCRIPT_NAME'] = script_path
        self.res = Response()
        self.user = Anonymous()

        self._init_default_response()

        self._init_paths()
        self._init_template_vars()
        self.lookup = build_lookup(self.storage)

        self._init_default_config()
        self._init_session()

    def _init_paths(self):
        path = self.req.path_info
        # remove the trailing "/" server-side, and other nice stuff
        path = self.SANITIZE_REGEXP.sub('/', path)
        path = posixpath.normpath(path)
        if path in ('.', '/'):
            path = ''

        if self.storage:
            f = self.storage.get_file(path)
        else:
            f = None

        # File object, related to the real one on the file system
        self.file = f
        self.object_type = f.get_object_type() if f else None

        query_vars = self.req.str_GET.items()
        # Path of the file relative to the Ass2m root
        self.path = path
        # Root application URL (useful for links to Actions)
        self.root_url = URL(self.req.script_name)
        # URL after Ass2m web application base URL
        self.relurl = URL(self.req.path_info, query_vars)
        # Complete URL (without host)
        self.url = URL(urlparse.urljoin(self.root_url.url, self.relurl.url[1:]), query_vars)

    def _init_default_config(self):
        if not self.storage:
            return
        config = self.storage.get_config()
        self.cookie_secret = config.data["web"].get("cookie_secret")
        try:
            if self.cookie_secret is None:
                self.cookie_secret = hexlify(new_secret())
                config.data["web"]["cookie_secret"] = self.cookie_secret
                config.save()
            # store the absolute root url (useful when in CLI)
            if not config.data["web"].get("root_url"):
                config.data["web"]["root_url"] = self.req.host_url + self.root_url.href
                config.save()
        except IOError:
            e = HTTPInternalServerError()
            self.template_vars.update({'scripts': [], 'stylesheets': []})
            e.body = self.render('error_writeconfig.html')
            raise e

    def _init_default_response(self):
        # defaults, may be changed later on
        self.res.status = 200
        self.res.headers['Content-Type'] = 'text/html; charset=UTF-8'
        self.res.cache_control.private = True

    def _init_template_vars(self):
        self.template_vars = build_vars(self.storage)
        # add and override variables specific to the web responses
        self.template_vars.update({
            'file': self.file,
            'path': self.path,
            'url': self.url,
            'root_url': self.root_url,
            'stylesheets': ['main.css'],
            'scripts': ['mootools-core-1.3.1.js', 'mootools-more-1.3.1.1.js', 'main.js'],
        })

    def render(self, template):
        return self.lookup.get_template(template).render(**self.template_vars)

    def respond(self):
        return self.res(self._environ, self._start_response)

    def iter_files(self):
        if self.object_type == "directory":
            for f in self.file.iter_children():
                if self.user.has_perms(f, f.PERM_LIST):
                    yield f

    def login(self, user, set_cookie=True):
        """
        Log in an user.
        user: User
        set_cookie: bool, to chose if we set the cookie to remember the user.

        Do note that if you replace the "res" attribute after,
        that the cookie will not be sent.
        """
        assert user.exists
        if set_cookie:
            signer = AuthCookieSigner(secret=self.cookie_secret, timeout=120*24*60)
            cookie = signer.sign(user.name)
            self.res.set_cookie('ass2m_auth', cookie,
                max_age=timedelta(days=120), httponly=True, path=quote_url(self.root_url))
            # ensure there is a session cookie
            self.update_session()
        self.user = user

    def logout(self, delete_cookie=True):
        """
        Log out the current user.
        delete_cookie: bool, to chose if we remove the cookie to forget the user.

        Do note that if you replace the "res" attribute after,
        that the cookie will not be removed.
        """
        if delete_cookie:
            self.res.delete_cookie('ass2m_auth', path=quote_url(self.root_url))
        self.user = Anonymous()

    def update_session(self):
        """
        Update the session cookie from the session attribute, encoded in plain JSON.
        It is not designed to be authoritative.
        JSON is readable client-side and allows us to restrict the types
        injected by the cookie compared to pickle.

        session should be a dict.

        Do note that if you replace the "res" attribute after,
        that the session cookie will not be sent.
        """
        self.res.set_cookie('ass2m_session', json.dumps(self.session),
            path=quote_url(self.root_url))

    def _init_session(self):
        """
        Get the session cookie. It must be a dict
        and will ignore invalid data.
        """
        try:
            session = json.loads(self.req.str_cookies.get('ass2m_session', ''))
        except ValueError:
            session = dict()
        else:
            if not isinstance(session, dict):
                session = dict()
        self.session = session


class Action(object):
    """
    REST action.
    Overload any HTTP method you wish. By default, head()
    will call get().
    """
    METHODS = ['HEAD', 'GET', 'POST', 'PUT', 'DELETE']

    def __init__(self, ctx):
        self.ctx = ctx

    def answer(self):
        """
        Find out the HTTP request method is and call the right
        method.
        For user agents that do not support PUT or DELETE, the _method parameter
        can be provided in either the POST data or the query string.
        """
        req = self.ctx.req
        method = req.method
        if method == 'POST':
            param_method = req.str_POST.get('_method')
            if param_method:
                # it's silly to simulate these requests with a _method param
                if param_method in ('HEAD', 'GET', 'POST'):
                    method = None
                else:
                    method = param_method
        if method in self.METHODS:
            return getattr(self, method.lower(), self._unhandled_method)()
        return self._unhandled_method()

    def head(self):
        return self.get()

    def get(self):
        return self._unhandled_method()

    def post(self):
        return self._unhandled_method()

    def put(self):
        return self._unhandled_method()

    def delete(self):
        return self._unhandled_method()

    def _unhandled_method(self):
        self.ctx.res = HTTPMethodNotAllowed()


class ViewAction(Action):
    pass


class WSGIMethodException(Exception):
    """
    Wrapper used to raise any WSGI application that is not an exception.
    """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        return self.app(environ, start_response)


class Dispatcher(object):
    def __init__(self, ctx):
        self.ctx = ctx
        self.basic_auther = AuthBasicAuthenticator(
            "ass2m at %s" % quote_url(ctx.root_url),
            self.basic_authfunc)

    def basic_authfunc(self, environ, username, password):
        """
        Auth function for AuthBasicAuthenticator.
        Allows to login by username/password, or if the username is _key,
        allows to login by key.
        """
        if username == '_key':
            for user in self.ctx.storage.iter_users():
                if password == user.key:
                    # hack to pass the real username
                    environ['key_username'] = user.name
                    return True
        user = self.ctx.storage.get_user(username)
        return user and user.is_valid_password(password)

    def _authenticate(self):
        ctx = self.ctx
        authkey = ctx.req.str_params.get('authkey')
        cookie = ctx.req.str_cookies.get('ass2m_auth')
        authby = ctx.req.str_params.get('authby')
        valid_user = None
        if authby == 'http':
            username = REMOTE_USER(ctx.req.environ)
            if not username:
                username = self.basic_auther(ctx.req.environ)
                if isinstance(username, str):
                    if username == '_key':
                        username = ctx.req.environ['key_username']
                    AUTH_TYPE.update(ctx.req.environ, 'basic')
                    REMOTE_USER.update(ctx.req.environ, username)
                    valid_user = ctx.storage.get_user(username)
                else:
                    raise WSGIMethodException(username.wsgi_application)
        if authkey:
            for user in ctx.storage.iter_users():
                if authkey == user.key:
                    # set the cookie for the following requests
                    valid_user = user
        elif cookie:
            signer = AuthCookieSigner(secret=ctx.cookie_secret)
            username = signer.auth(cookie)
            if username:
                valid_user = ctx.storage.get_user(username)
        if valid_user:
            ctx.login(valid_user, set_cookie='ass2m_session' not in ctx.req.str_cookies)

    def dispatch(self):
        ctx = self.ctx
        router = ctx.router

        if not ctx.storage:
            e = HTTPInternalServerError()
            ctx.template_vars.update({'scripts': [], 'stylesheets': []})
            if 'ASS2M_ROOT' in ctx.req.environ:
                ctx.template_vars['root'] = ctx.req.environ['ASS2M_ROOT']
                e.body = ctx.render('error_notworkingdir.html')
            else:
                e.body = ctx.render('error_norootpath.html')
            raise e

        self._authenticate()
        ctx.template_vars["user"] = ctx.user if ctx.user.exists else None

        # actions: not related to a file or directory
        # if we are in the root app URL
        if ctx.url.setvars().href == ctx.root_url.href:
            action = router.find_action(ctx.req.str_GET.get('action'))
            if action is not None:
                return action(ctx).answer()

        # check perms
        f = ctx.file
        if not ctx.user.has_perms(f, f.PERM_READ):
            raise HTTPForbidden()

        # normalize paths
        if ctx.object_type:
            goodpath = ctx.path
            if ctx.object_type == 'directory' and not goodpath.endswith('/'):
                # there should be a trailing slash in the client URL
                # for directories but not for files
                goodpath += '/'
            if ctx.req.path_info != goodpath:
                root_url = ctx.root_url.url
                if goodpath.startswith('/'):
                    goodpath = goodpath[1:]
                if not root_url.endswith('/'):
                    root_url += '/'
                goodlocation = URL(urlparse.urljoin(root_url, goodpath), vars=ctx.url.vars)
                ctx.res = HTTPFound(location=quote_url(goodlocation))
                return

        # no object type means no real file exists
        if ctx.object_type is None:
            raise HTTPNotFound('File not found')

        # find the action to forward the request to
        view, action = router.find_view(f, ctx.req.str_GET.get('view'))
        if view and action:
            # find out current action/view and available views
            ctx.template_vars['view'] = view.name
            ctx.template_vars['available_views'] = \
                sorted(router.get_available_views(f), key=str)
            return action(ctx).answer()

        # action/view not found
        raise HTTPNotFound('No route found')


class FileApp(PasteFileApp):
    def guess_type(self):
        # add UTF-8 by default to text content-types
        guess = PasteFileApp.guess_type(self)
        content_type = guess[0]
        if content_type and "text/" in content_type and "charset=" not in content_type:
            content_type += "; charset=UTF-8"
        return (content_type, guess[1])


class Server(object):
    def __init__(self, root=None):
        """
        The optional root parameter is used to force a root directory.
        If not present, the ASS2M_ROOT of environ (provided by the HTTP server)
        will be used.
        """
        self.root = root
        self.butt = Butt(router=Router())

    def bind(self, hostname, port):
        httpserver.serve(self.process, host=hostname, port=str(port))

    def process(self, environ, start_response):
        """
        WSGI interface
        """
        if self.root:
            environ.setdefault("ASS2M_ROOT", self.root)
        try:
            ctx = Context(self.butt, environ, start_response)
            Dispatcher(ctx).dispatch()
            return ctx.respond()
        except (HTTPError, WSGIMethodException), e:
            return e(environ, start_response)
