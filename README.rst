========
Fuselage
========

.. image:: https://travis-ci.org/yaybu/fuselage.png?branch=master
   :target: https://travis-ci.org/#!/yaybu/fuselage

.. image:: https://coveralls.io/repos/yaybu/fuselage/badge.png?branch=master
    :target: https://coveralls.io/r/yaybu/fuselage

.. image:: https://pypip.in/version/fuselage/badge.png
    :target: https://pypi.python.org/pypi/fuselage/


fuselage is a idempotent configuration bundle builder and runtime.

Use a simple python API to describe a server configuration and bundle that as a
script that can be executed on any system.

You can find us in #yaybu on irc.oftc.net.


Using with fabric
-----------------

You will need to install fabric explicitly. Fuselage does not depend on fabric.

You can write simple deployment scripts with Fabric by adding this to your fabfile::

    from fuselage.fabric import blueprint
    from fuselage.resources import *

    @blueprint
    def app_server():
        yield File(
            name='/tmp/some-thing'
        )

And then run it against multiple servers::

    fab -H server1,server2,server3 app_server

