#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ft=python et softtabstop=4 cinoptions=4 shiftwidth=4 ts=4 ai

from flup.server.fcgi import WSGIServer

def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    yield """
<html>
<head>
    <title>Hello you!</title>
</head>
<body>
    <h1>Hello you!</h1>
</body>
</html>"""

WSGIServer(app).run()
