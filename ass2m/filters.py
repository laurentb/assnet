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


from urlparse import urlsplit, urlunsplit
from urllib import quote
from paste.url import URL

def compact(text):
    return text.replace('\n', ' ').strip()

def quote_url(url):
    """
    Quote the path part of an URL object and return the full URL as a string.
    """
    purl = urlsplit(url.url)
    qpath = quote(purl.path)
    # queries should not be in the URL, it means it's a '?' in a file
    if purl.query:
        qpath += quote('?'+purl.query)
    purl = urlunsplit((
        purl.scheme,
        purl.netloc,
        qpath,
        '',
        purl.fragment))
    return URL(purl, vars=url.vars).href
