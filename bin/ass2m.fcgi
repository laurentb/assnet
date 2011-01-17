#!/usr/bin/env python
from flup.server.fcgi import WSGIServer
from ass2m.server import Server

server = Server('/tmp/ass2m')
WSGIServer(server.process).run()
