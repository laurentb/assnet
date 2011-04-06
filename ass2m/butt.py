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


import os
import re

from .plugin import Plugin


__all__ = ['Butt']


class Butt(object):
    def __init__(self, parser=None, router=None):
        self.parser = parser
        self.router = router
        self.load_plugins()

    def iter_existing_plugin_names(self):
        try:
            import plugins
        except ImportError:
            return
        for path in plugins.__path__:
            regexp = re.compile('([\w\d_]+).py$')
            for f in os.listdir(path):
                m = regexp.match(f)
                if m and m.group(1) != '__init__':
                    yield m.group(1)

    def load_plugins(self):
        self.plugins = {}
        for existing_plugin_name in self.iter_existing_plugin_names():
            self.load_plugin(existing_plugin_name)

    def load_plugin(self, plugin_name):
        package_name = 'ass2m.plugins.%s' % plugin_name
        package = __import__(package_name, fromlist=[str(package_name)])

        klass = None
        for attrname in dir(package):
            attr = getattr(package, attrname)
            if isinstance(attr, type) and issubclass(attr, Plugin) and attr != Plugin:
                klass = attr
                break

        if not klass:
            return

        plugin = klass(self)
        plugin.init()
        self.plugins[plugin_name] = plugin
