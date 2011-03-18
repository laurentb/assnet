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
import re

from .storage import Storage
from .plugin import Plugin


__all__ = ['Ass2m']


class Ass2m(object):
    DIRNAME = '.ass2m'
    VERSION = '1.0-dev'
    COPYRIGHT = 'Copyright(C) 2011 Romain Bignon, Laurent Bachelier'

    def __init__(self, path, parser=None, router=None):
        if isinstance(path, Storage):
            storage = path
        elif path:
            try:
                while not self.DIRNAME in os.listdir(path) and path != os.path.dirname(path):
                    path = os.path.dirname(path)
            except OSError:
                path = None
            if path and path != os.path.dirname(path):
                storage = Storage(os.path.join(path, self.DIRNAME))
            else:
                storage = None
        else:
            storage = None

        self.parser = parser
        self.router = router
        self.storage = storage
        if self.storage:
            self.root = os.path.realpath(os.path.join(storage.path, os.path.pardir))
        else:
            self.root = None

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

    def create(self, path):
        self.storage = Storage.init(os.path.join(path, self.DIRNAME))
        self.root = os.path.realpath(os.path.join(self.storage.path, os.path.pardir))
