========
Fuselage
========

.. image:: https://travis-ci.org/yaybu/fuselage.png?branch=master
   :target: https://travis-ci.org/#!/yaybu/fuselage

.. image:: https://ci.appveyor.com/api/projects/status/o00q9mf5plhmquk3?svg=true
   :target: https://ci.appveyor.com/project/yaybu/fuselage

.. image:: https://coveralls.io/repos/yaybu/fuselage/badge.png?branch=master
    :target: https://coveralls.io/r/yaybu/fuselage

.. image:: https://pypip.in/version/fuselage/badge.png
    :target: https://pypi.python.org/pypi/fuselage/

.. image:: https://readthedocs.org/projects/fuselage/badge/?version=latest
    :target: http://docs.yaybu.com/projects/fuselage/en/latest/


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
    def minecraft(bundle):
        yield Directory(
            name='/var/local/minecraft',
        )
        yield Execute(
            command='wget https://s3.amazonaws.com/Minecraft.Download/versions/1.8/minecraft_server.1.8.jar',
            cwd="/var/local/minecraft",
            creates="/var/local/minecraft/minecraft_server.1.8.jar",
        )
        yield File(
            name='/var/local/minecraft/server.properties',
            contents=open('var_local_minecraft_server.properties').read(),
        )
        yield File(
            name="/etc/systemd/system/minecraft.service",
            contents=open("etc_systemd_system_minecraft.service"),
        )
        yield Execute(
            command="systemctl daemon-reload",
            watches=['/etc/systemd/system/minecraft.service'],
        )
        yield Execute(
            command="systemctl restart minecraft.service",
            watches=[
                "/var/local/minecraft/server.properties",
                "/etc/systemd/system/minecraft.service",
            ]
        )

And then run it against multiple servers::

    fab -H server1,server2,server3 minecraft

