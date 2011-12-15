from ass2m.filters import quote_url
from paste.url import URL
from unittest import TestCase


class FiltersTest(TestCase):
    def test_quote(self):
        assert quote_url(URL('http://ass2m.org/')) \
                == 'http://ass2m.org/'
        assert quote_url(URL('http://ass2m.org:42/')) \
                == 'http://ass2m.org:42/'
        assert quote_url(URL('22:42:01.JPG').setvars(view='thumbnail')) \
                == '22%3A42%3A01.JPG?view=thumbnail'
        assert quote_url(URL('http://ass2m.org/22:42:01.JPG').setvars(view='thumbnail')) \
                == 'http://ass2m.org/22%3A42%3A01.JPG?view=thumbnail'
        assert quote_url(URL('http://ass2m.org:42/22:42:01.JPG').setvars(view='thumbnail')) \
                == 'http://ass2m.org:42/22%3A42%3A01.JPG?view=thumbnail'
