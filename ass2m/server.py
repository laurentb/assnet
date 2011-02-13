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
from webob import Request, Response
from webob.exc import HTTPFound, HTTPNotFound, HTTPForbidden
from paste import httpserver
from paste.fileapp import FileApp
from mako.lookup import TemplateLookup
from paste.auth.cookie import AuthCookieSigner, new_secret

from ass2m import Ass2m
from users import Anonymous

COOKIE_SECRET = new_secret()

class Ass2mFileApp(FileApp):
    def guess_type(self):
        # add UTF-8 by default to text content-types
        guess = FileApp.guess_type(self)
        content_type = guess[0]
        if content_type and "text/" in content_type and "charset=" not in content_type:
            content_type += "; charset=UTF-8"
        return (content_type, guess[1])

class Actions(object):
    def __init__(self, environ, start_response):
        self.ass2m = Ass2m(environ.get("ASS2M_ROOT", None))
        self._environ = environ
        self._start_response = start_response
        self.req = Request(environ)
        self.res = Response()
        self.user = Anonymous()

        paths = [os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data')),
                 '/usr/share/ass2m',
                 '/usr/local/share/ass2m']
        self.lookup = TemplateLookup(directories=['%s/templates' % path for path in paths],
                                     collection_size=20,
                                     output_encoding='utf-8')

        # defaults, may be changed later on
        self.res.status = 200
        self.res.headers['Content-Type'] = 'text/html; charset=UTF-8';


    def error_notworkingdir(self):
        self.res.status = 500
        if self._environ.has_key("ASS2M_ROOT"):
            self.res.body = self.lookup.get_template('error_notworkingdir.html'). \
                        render(root=self._environ["ASS2M_ROOT"])
        else:
            self.res.body = self.lookup.get_template('error_norootpath.html'). \
                        render()

        return self.res(self._environ, self._start_response)


    def answer(self):
        if not self.ass2m.storage:
            return self.error_notworkingdir()

        relpath = self.req.path_info
        fpath = os.path.join(self.ass2m.root, relpath[1:])
        if self.req.path_info == '/LOGIN':
            return self.authenticate()

        if os.path.isdir(fpath):
            if self.req.path_info[-1] != '/':
                self.res = HTTPFound(add_slash=True)
                return self.res(self._environ, self._start_response)
            if relpath[-1] == '/':
                # skip the terminated /
                relpath = os.path.dirname(relpath)

        # check perms
        f = self.ass2m.storage.get_file(relpath)
        if not self.user.has_perms(f, f.PERM_READ):
            self.res = HTTPForbidden()
            return self.res(self._environ, self._start_response)

        if os.path.isfile(fpath):
            # serve the file, delegate everything to to FileApp
            self.res = Ass2mFileApp(fpath)
            return self.res(self._environ, self._start_response)
        elif os.path.isdir(fpath):
            return self.listdir(relpath)
        else:
            self.res = HTTPNotFound()
            return self.res(self._environ, self._start_response)


    def listdir(self, relpath):
        directory = os.path.join(self.ass2m.root, relpath[1:])
        dirs = []
        files = []
        for filename in sorted(os.listdir(directory)):
            f = self.ass2m.storage.get_file(os.path.join(relpath, filename))
            if not self.user.has_perms(f, f.PERM_LIST):
                continue
            if os.path.isdir(os.path.join(directory, filename)):
                dirs.append(filename.decode('utf-8'))
            else:
                files.append(filename.decode('utf-8'))

        self.res.body = self.lookup.get_template('list.html'). \
                    render(dirs=dirs, files=files, relpath=relpath)
        return self.res(self._environ, self._start_response)


    def authenticate(self):
        signer = AuthCookieSigner(secret=COOKIE_SECRET)
        user = self.req.str_GET.get('user')
        if user:
            cookie = signer.sign(user)
            self.res.set_cookie('ass2m_auth', cookie)
        else:
            cookie = self.req.str_cookies.get('ass2m_auth')
            user = signer.auth(cookie)

        if user:
            page = '<html><body>Welcome %s</body></html>' % user
        else:
            page = ('<html><body><form><input name="user" />'
                    '<input type="submit" /></form></body></html>')
        self.res.body = page

        return self.res(self._environ, self._start_response)

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
        actions = Actions(environ, start_response)
        return actions.answer()

