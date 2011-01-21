# -*- coding: utf-8 -*-

import os
from webob import Request
from webob.exc import HTTPMovedPermanently, HTTPNotFound
from paste import httpserver
from paste.fileapp import FileApp

from ass2m import Ass2m, NotWorkingDir

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
        self.user = None

    def error_notworkingdir(self):
        self.start_response('500 ERROR', [('Content-Type', 'text/html; charset=UTF-8')])
        if self.environ.has_key("ASS2M_ROOT"):
            return """
    <html>
    <head>
        <title>Error</title>
    </head>
    <body>
    <h1>Internal error</h1>
    <p>
    The configured root path is not an ass2m working directory.<br />
    Please use:
    </p>
    <pre>$ cd %s && ass2m init</pre>
    <hr>
    <address>ass2m</address>
    </body>
    </html>""" % self.environ["ASS2M_ROOT"]
        else:
            return """
    <html>
    <head>
        <title>Error</title>
    </head>
    <body>
    <h1>Internal error</h1>
    <p>
    No root path was provided.
    </p>
    <hr>
    <address>ass2m</address>
    </body>
    </html>"""


    def answer(self):
        if not self.ass2m:
            return self.error_notworkingdir()

        parsed_path = self.req.path_info[1:]
        fpath = os.path.join(self.ass2m.root, parsed_path)
        if os.path.isfile(fpath):
            fapp = Ass2mFileApp(fpath)
            # serve the file, delegate everything to to FileApp
            return fapp(self.environ, self.start_response)

        if os.path.isdir(fpath):
            if parsed_path[-1:] != "/" and len(parsed_path):
                resp = HTTPMovedPermanently(location=self.req.path_info+"/")
                return resp(self.environ, self.start_response)
            else:
                return self.listdir(parsed_path)

        resp = HTTPNotFound()
        return resp(self.environ, self.start_response)

    def listdir(self, relpath):
        directory = os.path.join(self.ass2m.root, relpath)
        self.start_response('200 OK', [('Content-Type', 'text/html; charset=UTF-8')])
        yield """
<html>
<head>
    <title>Index of /%s</title>
</head>
<body>
<h1>Listing /%s</h1>
<ul>""" % (relpath, relpath)
        for filename in sorted(os.listdir(directory)):
            f = self.ass2m.get_file(os.path.join(directory, filename))
            if self.user and not self.user.has_perms(f):
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
    def __init__(self, root = None):
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

