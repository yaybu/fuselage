Fabric
======

The ``fuselage`` module comes with fabric integration. This is simple a decorator that allows you to simple ``yield`` resources and apply them to any hosts fabric can connect to.

For example in your ``fabfile.py`` you might write::

    from fuselage.fabric import blueprint
    from fuselage.resources import *

    @blueprint
    def app_server():
        """ Deploy configuration to app server cluster """
        yield File(
            name='/tmp/some-thing'
        )
        yield Package(name="apache2")

This task will show up in your fabric task list like any other::

    # fab -l
    Available commands:

        app_server  Deploy configuration to app server cluster


You can run this against multiple computers::

    # fab -H server1,server2 app_server
