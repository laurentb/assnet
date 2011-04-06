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

from urlparse import urlparse, urlunparse
from urllib import quote
from paste.url import URL

def compact(text):
    return text.replace('\n', ' ').strip()

def quote_url(url):
    """
    Quote the path part of an URL object and return the full URL as a string.
    """
    purl = urlparse(url.url)
    purl = urlunparse((purl.scheme, purl.netloc, quote(purl.path), purl.params, purl.query, purl.fragment))
    return URL(purl, vars=url.vars).href
