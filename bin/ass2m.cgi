#!/usr/bin/env python
from wsgiref.handlers import CGIHandler
from ass2m.server import Server

server = Server('/tmp/ass2m')
CGIHandler().run(server.process)
