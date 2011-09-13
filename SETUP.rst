This file sums up the various way of setting up ass2m with a full-blown HTTP server.

Lighttpd, CGI
-------------

This mode is not the best for performance, but it won't take any memory when not used.

You will need to load the ``alias``, ``setenv`` and ``cgi`` modules for this setup to work.
If they are not loaded, the following directives will be ignored.

Let's say you want http://your.host/data/ to be served by Ass2m. Add this to your ``lighttpd.conf``::

    $HTTP["host"] == "your.host" {
        $HTTP["url"] =~ "^/data" {
            # make everything go through ass2m
            alias.url = ( "" => "/usr/share/ass2m/scripts/ass2m.cgi" )
            cgi.assign = ( "ass2m.cgi" => "" )
            # configure ass2m
            setenv.add-environment = (
                "FORCE_SCRIPT_NAME" => "/data",
                "ASS2M_ROOT" => "/path/to/the/work/dir",
            )
        }
    }

Please adjust the paths. You can make use of the ``setenv`` directive to set a different ``PYTHONPATH``.
The should be no ``/`` at the end of the value of ``FORCE_SCRIPT_NAME``.

If you just want a whole host to be served by Ass2m, you can use a simpler configuration::

    $HTTP["host"] == "your.host" {
        # make everything go through ass2m
        alias.url = ( "" => "/usr/share/ass2m/scripts/ass2m.cgi" )
        cgi.assign = ( "ass2m.cgi" => "" )
        # configure ass2m
        setenv.add-environment = (
            "ASS2M_ROOT" => "/path/to/the/work/dir",
        )
    }

Lighttpd, FastCGI
-----------------

This is the fastest mode as instances are not started for each request. It also allows Ass2m to delegate the file transfer as soon as possible to the web server, which is much more efficient at that task.

In this example, the FastCGI server is started by lighttpd::

    $HTTP["host"] == "your.host" {
        fastcgi.server = (
            "/data" => ((
                "bin-path" => "/usr/share/ass2m/scripts/ass2m.fcgi",
                "socket" => "/tmp/ass2m.sock",
                "check-local" => "disable",
                "allow-x-send-file" => "enable",
           ))
        )

        $HTTP["url"] =~ "^/data" {
            setenv.add-environment = (
             "ASS2M_ROOT" => "/path/to/the/work/dir",
             "SERVER_SENDFILE" => "lighttpd",
           )
         }
    }

We are again serving http://your.host/data/ through Ass2m. To serve the whole host::

    $HTTP["host"] == "your.host" {
        fastcgi.server = (
            "" => ((
                "bin-path" => "/usr/share/ass2m/scripts/ass2m.fcgi",
                "socket" => "/tmp/ass2m.sock",
                "check-local" => "disable",
                "allow-x-send-file" => "enable",
           ))
        )

        setenv.add-environment = (
         "ASS2M_ROOT" => "/path/to/the/work/dir",
         "FORCE_SCRIPT_NAME" => "",
         "SERVER_SENDFILE" => "lighttpd",
    }

``allow-x-send-file`` and ``SERVER_SENDFILE`` are related and optionnal, but will provide much faster file transfers in the future.

You should check out directives like ``max-procs`` to adjust the number of processes, and ``bin-environment`` to change the ``PYTHONPATH``.
