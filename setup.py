#!/usr/bin/env python

from setuptools import setup, find_packages
from glob import glob
from sys import version_info

assert version_info >= (2, 6)
DATA_DIR = 'share/assnet'
REQUIREMENTS = ['PIL', 'mako', 'webob', 'paste', 'PyRSS2Gen', 'python-dateutil']
if version_info < (2, 7):
    REQUIREMENTS.append('argparse')

setup(name="assnet",
    version='0.1',
    description='The Asocial Sharing Network project is a web application useful for sharing files (with support for photos galleries, videos, etc.) or organizing events with your friends, removing the obligation of using Facebook or other centralized social networks. It is configurable and administrable by geeks, yet easy to use by their mothers.',
    long_description=open('README.rst').read(),
    author='Laurent Bachelier',
    author_email='laurent@bachelier.name',
    url='http://assnet.org/',
    license='GNU AGPL 3',
    classifiers=[
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: JavaScript',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],

    zip_safe=False,
    packages=find_packages(),
    scripts=['bin/asn', 'bin/assnet-serve'],
    data_files=[
        ('%s/assets' % DATA_DIR,    glob('data/assets/*')),
        ('%s/templates' % DATA_DIR, glob('data/templates/*')),
        ('%s/scripts' % DATA_DIR,   glob('data/scripts/*')),
    ],
    install_requires=REQUIREMENTS,
    test_suite='nose.collector',
    tests_require=['nose>=1.0', 'webtest'],
)
