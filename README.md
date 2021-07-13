# Fuselage

fuselage is a simple and fast idempotent configuration bundle builder and runtime.

To use fuselage:

* Use your code to build a configuration bundle via our API. The output is an executable payload. 
* Transfer that payload to your server.
* Run it.

It's fast. Unlike some configuration management tools the entire process runs on the target. It doesn't rely on a round trip between every step.

It's small. It's only dependency is a python3 interpreter on the target systemm plus some common posix binaries.

It's secure. It doesn't bring it's on control plane that you need to understand in detail to properly secure.

It's simple. It provides the absolute minimum, and tries to get out the way for the stuff where it doesn't need to have an opinion. Bring your own template engine, or don't use one at all.  Bring your own control plane. Run it from a deamonset, run it via fabric or even just use scp and run it by hand.


## Using with fabric

You will need to install fabric explicitly. Fuselage does not depend on fabric.

You can write simple deployment scripts with Fabric by adding this to your fabfile:

```python
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
```

And then run it against multiple servers::

```bash
fab -H server1,server2,server3 minecraft
```
