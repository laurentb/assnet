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


from urlparse import urlsplit
from urllib import quote
from paste.url import URL

__all__ = ['compact', 'quote_url', 'quote_path', 'quote_and_decode_url']

UNSAFE_CHARS = {
    '?': quote('?'),
    '&': quote('&'),
    ';': quote(';'),
    ',': quote(','),
    '=': quote('='),
    ' ': quote(' '),
    '+': quote('+'),
    ':': quote(':'),
    '$': quote('$'),
}

def compact(text):
    return text.replace('\n', ' ').strip()

def quote_path(path):
    """
    Quote a path (see quote_url)
    """
    return ''.join([UNSAFE_CHARS.get(c, c) for c in path])

def quote_url(url):
    """
    Quote the path part of an URL object and return the full URL as a string.
    Special characters in the URL are not considered as the query string or any other
    parameters, they should be in their dedicated variables of the URL class.
    """
    purl = urlsplit(url.url)
    # we do not support escaping an URL with a scheme and netloc yet
    assert not purl.scheme and not purl.netloc
    return URL(quote_path(url.url), vars=url.vars).href

def quote_and_decode_url(url):
    """
    Like quote_url but for usage in Mako templates
    """
    return quote_url(url).decode('utf-8')
