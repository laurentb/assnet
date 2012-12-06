This file sums up the various way of setting up assnet with a full-blown HTTP server.

Lighttpd, CGI
-------------

This mode is not the best for performance, but it won't take any memory when not used.

You will need to load the ``alias``, ``setenv`` and ``cgi`` modules for this setup to work.
If they are not loaded, the following directives will be ignored.

Let's say you want http://your.host/data/ to be served by assnet. Add this to your ``lighttpd.conf``::

    $HTTP["host"] == "your.host" {
        $HTTP["url"] =~ "^/data" {
            # make everything go through assnet
            alias.url = ( "" => "/usr/share/assnet/scripts/assnet.cgi" )
            cgi.assign = ( "assnet.cgi" => "" )
            # configure assnet
            setenv.add-environment = (
                "FORCE_SCRIPT_NAME" => "/data",
                "ASSNET_ROOT" => "/path/to/the/work/dir",
            )
        }
    }

Please adjust the paths. You can make use of the ``setenv`` directive to set a different ``PYTHONPATH``.
The should be no ``/`` at the end of the value of ``FORCE_SCRIPT_NAME``.

If you just want a whole host to be served by assnet, you can use a simpler configuration::

    $HTTP["host"] == "your.host" {
        # make everything go through assnet
        alias.url = ( "" => "/usr/share/assnet/scripts/assnet.cgi" )
        cgi.assign = ( "assnet.cgi" => "" )
        # configure assnet
        setenv.add-environment = (
            "ASSNET_ROOT" => "/path/to/the/work/dir",
        )
    }

Lighttpd, FastCGI
-----------------

This is the fastest mode as instances are not started for each request. It also allows assnet to delegate the file transfer as soon as possible to the web server, which is much more efficient at that task.

In this example, the FastCGI server is started by lighttpd::

    $HTTP["host"] == "your.host" {
        fastcgi.server = (
            "/data" => ((
                "bin-path" => "/usr/share/assnet/scripts/assnet.fcgi",
                "socket" => "/tmp/assnet.sock",
                "check-local" => "disable",
                "allow-x-send-file" => "enable",
           ))
        )

        $HTTP["url"] =~ "^/data" {
            setenv.add-environment = (
             "ASSNET_ROOT" => "/path/to/the/work/dir",
             "SERVER_SENDFILE" => "lighttpd",
           )
         }
    }

We are again serving http://your.host/data/ through assnet. To serve the whole host::

    $HTTP["host"] == "your.host" {
        fastcgi.server = (
            "" => ((
                "bin-path" => "/usr/share/assnet/scripts/assnet.fcgi",
                "socket" => "/tmp/assnet.sock",
                "check-local" => "disable",
                "allow-x-send-file" => "enable",
           ))
        )

        setenv.add-environment = (
         "ASSNET_ROOT" => "/path/to/the/work/dir",
         "FORCE_SCRIPT_NAME" => "",
         "SERVER_SENDFILE" => "lighttpd",
    }

``allow-x-send-file`` and ``SERVER_SENDFILE`` are related and optionnal, but will provide much faster file transfers in the future.

You should check out directives like ``max-procs`` to adjust the number of processes, and ``bin-environment`` to change the ``PYTHONPATH``.
