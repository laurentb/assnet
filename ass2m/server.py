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
from webob import Request
from webob.exc import HTTPMovedPermanently, HTTPNotFound, HTTPForbidden
from paste import httpserver
from paste.fileapp import FileApp
from mako.lookup import TemplateLookup

from ass2m import Ass2m, NotWorkingDir
from users import Anonymous

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
        try:
            self.ass2m = Ass2m(environ.get("ASS2M_ROOT"))
        except NotWorkingDir:
            self.ass2m = None
        self.environ = environ
        self.req = Request(environ)
        self.start_response = start_response
        self.user = Anonymous()

        # TODO find a way to locate template directories
        self.lookup = TemplateLookup(directories=['data/templates'],
                                    collection_size=20,
                                    output_encoding='utf-8')


    def error_notworkingdir(self):
        self.start_response('500 ERROR', [('Content-Type', 'text/html; charset=UTF-8')])
        if self.environ.has_key("ASS2M_ROOT"):
            return self.lookup.get_template('error_notworkingdir.html'). \
                        render(root=self.environ["ASS2M_ROOT"])
        else:
            return self.lookup.get_template('error_norootpath.html'). \
                        render()


    def answer(self):
        if not self.ass2m:
            return self.error_notworkingdir()

        relpath = self.req.path_info
        fpath = os.path.join(self.ass2m.root, relpath[1:])

        if os.path.isdir(fpath):
            if self.req.path_info[-1:] != '/':
                resp = HTTPMovedPermanently(location=self.req.path_info+"/")
                return resp(self.environ, self.start_response)
            if relpath[-1] == '/':
                # skip the terminated /
                relpath = os.path.dirname(relpath)

        # check perms
        f = self.ass2m.storage.get_file(relpath)
        if not self.user.has_perms(f, f.PERM_READ):
            resp = HTTPForbidden()
            return resp(self.environ, self.start_response)

        if os.path.isfile(fpath):
            fapp = Ass2mFileApp(fpath)
            # serve the file, delegate everything to to FileApp
            return fapp(self.environ, self.start_response)
        elif os.path.isdir(fpath):
            return self.listdir(relpath)
        else:
            resp = HTTPNotFound()
            return resp(self.environ, self.start_response)

    def listdir(self, relpath):
        directory = os.path.join(self.ass2m.root, relpath[1:])
        self.start_response('200 OK', [('Content-Type', 'text/html; charset=UTF-8')])
        yield """
<html>
<head>
    <title>Index of %s</title>
</head>
<body>
<h1>Listing %s</h1>
<ul>""" % (relpath, relpath)
        for filename in sorted(os.listdir(directory)):
            f = self.ass2m.storage.get_file(os.path.join(relpath, filename))
            if not self.user.has_perms(f, f.PERM_LIST):
                continue
            if os.path.isdir(os.path.join(directory, filename)):
                yield '<li><strong><a href="%s/">%s/</a></strong></li>' % (filename, filename)
            else:
                yield '<li><a href="%s">%s</a></li>' % (filename, filename)
        yield """
</ul>
<hr>
<address>ass2m</address>
</body>
</html>"""

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

