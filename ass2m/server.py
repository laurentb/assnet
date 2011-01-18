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

class Server(object):
    def __init__(self, root):
        self.root = root
        try:
            self.ass2m = Ass2m(root)
        except NotWorkingDir:
            self.ass2m = None

    def bind(self, hostname, port):
        httpserver.serve(self.process, host=hostname, port=str(port))

    def process(self, environ, start_response):
        if not self.ass2m:
            try:
                self.ass2m = Ass2m(self.root)
            except NotWorkingDir:
                return self.error_notworkingdir(start_response)

        req = Request(environ)
        parsed_path = req.path_info[1:]
        fpath = os.path.join(self.root, parsed_path)
        if os.path.isfile(fpath):
            fapp = Ass2mFileApp(fpath)
            # serve the file, delegate everything to to FileApp
            return fapp(environ, start_response)

        if os.path.isdir(fpath):
            if parsed_path[-1:] != "/" and len(parsed_path):
                resp = HTTPMovedPermanently(location=req.path_info+"/")
                return resp(environ, start_response)
            else:
                return self.listdir(start_response, parsed_path)

        resp = HTTPNotFound()
        return resp(environ, start_response)

    def listdir(self, start_response, relpath):
        directory = os.path.join(self.root, relpath)
        start_response('200 OK', [('Content-Type', 'text/html; charset=UTF-8')])
        yield """
<html>
<head>
    <title>Index of /%s</title>
</head>
<body>
<h1>Listing /%s</h1>
<ul>""" % (relpath, relpath)
        for filename in sorted(os.listdir(directory)):
            if filename.startswith('.'):
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

    def error_notworkingdir(self, start_response):
        start_response('500 ERROR', [('Content-Type', 'text/html; charset=UTF-8')])
        yield """
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
<pre>$ ass2m init %s</pre>
<hr>
<address>ass2m</address>
</body>
</html>""" % self.root
