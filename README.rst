The *Authenticated Social Storage Made for Mothers* (ass2m) project is a web application useful for sharing files (with support for photos galleries, videos, etc.) or organizing events with your friends, removing the obligation of using centralized social networks.

You self-host your data and manage permissions to protect your privacy and control exactly who can access what information.

Your contacts go a web interface to see and interact with your data, and you use a command-line tool to control your space.

Overview
--------

The command-line interface is a first-class citizen in ass2m. It is the main way of setting up an ass2m instance.

The software is able to send emails, and a friendly web interface is provided to end-users. The goal is to enable advanced sharing features while staying as close as possible to the Internet standards (web standards, email, etc.).

Features
--------

* Easy to set-up, you create a working directory on your system and share it with a simple configuration on your HTTP daemon.
* Permissions are always in mind, to control your privacy.
* Your contacts aren't required to keep a login/password.
* Notifications are sent by mail.
* A key (OTP) system is used to give to your contacts URLs with a token to authenticate them.
* For each file or directory, you can choose what default view to use (HTML list, text list, JSON, gallery, downloadable archive, etc. for a directory).
* Support several plugins to provide extra features.
* Thorough automated testing, making it PHB-compliant.

ass2m is written in Python and is distributed under the AGPLv3+ license.

Installation
------------

Dependencies
~~~~~~~~~~~~

* Python >= 2.6
* python-paste
* python-webob
* python-mako
* python-imaging
* python-argparse or Python >= 2.7

Those dependencies will be either checked or installed automatically unless you chose the "No installation" method.

With a package (recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Gentoo has an ass2m ebuild in the laurentb overlay. To install::

    # layman -a laurentb
    # emerge --autounmask -av ass2m

From the sources
~~~~~~~~~~~~~~~~

Get the source code from the git repository and run the installer::

    $ git clone git://git.symlink.me/pub/laurentb/ass2m.git
    $ cd ass2m
    $ sudo python setup.py install

No installation (development)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You just have to set the PYTHONPATH variable.
For instance, to run the ass2m CLI::

    $ git clone git://git.symlink.me/pub/laurentb/ass2m.git
    $ cd ass2m
    $ PYTHONPATH=. ./bin/ass2m

Beware that if you also have installed ass2m globally, the installed data files (assets, templates) could be used (the local ones of course have an higher priority).
