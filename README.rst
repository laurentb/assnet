The *Authenticated Social Storage Made for Mothers* (ass2m) project is a web application useful for sharing files (with support for photos galleries, videos, etc.) or organizing events with your friends, removing the obligation of using centralized social networks.

You self-host your data and manage permissions to protect your privacy and control exactly who can access what information.

Your contacts go to a web interface to see and interact with your data, and you use a command-line tool to control your space.

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
* python-argparse or Python >= 2.7
* python-paste
* python-webob
* python-mako
* python-imaging
* python-pyrss2gen

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

Getting started
---------------

First, we have to create the *working directory* where all files you want to share will be put.::

    $ cd mysharedfiles
    $ ass2m init
    Ass2m working directory created.

You can test ass2m *right now* by starting the integrated server. However, for a more serious usage, it is recommended to configure it to work with a full-blown web server (see the Configuration section)::

    $ ass2m-serve .
    serving on 0.0.0.0:8042 view at http://127.0.0.1:8042

You can now play around with the web interface. Add some files in your working directory, and they will appear. For instance, let's add one file::

    $ cp ~/pics/my_gf_naked.jpg ./

Refresh the web page. By default, since we added an image, it will be shown as a thumbnail.
However, you might not want this picture to be seen by everyone::

    $ ass2m chmod all -irl my_gf_naked.jpg

Check all set permissions::

    $ ass2m tree
    -/                                       all(irl-)
     |-.ass2m/                               all(----)
     -my_gf_naked.jpg                        all(----)

``all`` is a special name to refer to everyone (anonymous users being part of it of course). ``i`` is for appearing In a list, ``r`` is for Reading, ``w`` is for Writing, and ``l`` is for Listing a directory. All modes are inherited from the parents if they are not specified at a higher level.

Refresh the web page. Now, no one can read and or even know that file exists. But let's do something fun!::

    $ ass2m chmod all +i my_gf_naked.jpg
    $ ass2m tree
    -/                                       all(irl-)
     |-.ass2m/                               all(----)
     -my_gf_naked.jpg                        all(i---)

Refresh the web page. The file will appear, but if you try to view it, you will be denied.

The next step is to allow only some users to view that file::

    $ ass2m contacts add myfriend
    $ ass2m chmod u.myfriend +ir my_gf_naked.jpg
    $ ass2m tree
    -/                                       all(irl-)
     |-.ass2m/                               all(----)
     -my_gf_naked.jpg                        u.myfriend(ir--) all(i---)

``u`` is a prefix to specify it concerns an user.

Now, connect as this user::

    $ ass2m contacts genkey myfriend
    Key of user myfriend set to 455b00b1e5.
    $ ass2m geturl -u myfriend .
    http://127.0.0.1:8042/?authkey=455b00b1e5

Open the URL. You can now access the file!
