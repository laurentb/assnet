# -*- coding: utf-8 -*-

# Copyright (C) 2011 Romain Bignon, Laurent Bachelier
#
# This file is part of assnet.
#
# assnet is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# assnet is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with assnet. If not, see <http://www.gnu.org/licenses/>.

import os

from mako.lookup import TemplateLookup
from paste.url import URL
from urlparse import urlsplit, urlunsplit

from .storage import Storage
from .version import VERSION


def build_lookup(storage):
    """
    Get the Mako TemplateLookup.
    If a Storage object is provided (it should be most of the time),
    it will also use its data directory.
    """
    data_paths = storage.DATA_PATHS if storage else Storage.DATA_PATHS
    paths = [os.path.join(path, 'templates') for path in data_paths]
    imports = ['from assnet.filters import compact as cpt, quote_and_decode_url as U',
            'from paste.url import URL']
    return TemplateLookup(directories=paths, collection_size=20,
                     output_encoding='utf-8', input_encoding='utf-8',
                     default_filters=['decode.utf8'],
                     imports=imports)


def build_vars(storage):
    """
    Get useful default variables to use with Mako templates.
    If a Storage object is provided (it should be most of the time),
    it will set a root_url, which is useful when outside of the web server.
    """
    return {
        'assnet_version': VERSION,
        'root_url': build_root_url(storage),
        'global': dict(),
    }


def build_root_url(storage):
    """
    Try to build a root URL from the Storage instance.
    If not possible it returns None.
    """
    if storage:
        root_url = storage.get_config().data['web'].get('root_url')
        if root_url:
            # convert the root_url to dumb str (configs are unicode)
            return URL(root_url.encode('utf-8'))


def build_url(root_url, f, user=None, use_key=True, http_auth=False):
    """
    Build an URL for a particular file and user if provided.
    root_url: URL (paste.url)
    f: File
    user: User
    use_key: Add the user key to the URL if possible
    http_auth: Make an URL for HTTP authentication (for downloaders for instance)
    """
    qs = {}
    if http_auth:
        qs['authby'] = 'http'
        purl = urlsplit(root_url.url)
        netloc = purl.netloc
        if use_key and user and user.key:
            netloc = '%s:%s@%s' % ('_key', user.key, netloc)
        elif user and user.password:
            netloc = '%s@%s' % (user.name, netloc)
        root_url = URL(urlunsplit((purl.scheme, netloc, purl.path, purl.query, purl.fragment)))
    elif use_key and user and user.key:
        qs['authkey'] = user.key
    path = f.path
    if f.isdir():
        path += '/'
    return root_url.addpath(path).setvars(**qs)
