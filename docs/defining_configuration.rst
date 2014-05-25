======================
Defining configuration
======================

Resource bundles
================

A fuselage bundle is a list of resources to manage and the configuration to apply to them. You use the ``add`` method to build a bundle::

    from fuselage.bundle import ResourceBundle
    from fuselage.resources import *

    bundle = ResourceBundle()
    bundle.add(Package(name="apache2"))

You can assemble a bundle into a compressed archive using a builder object::

    from fuselage.builder import Builder

    builder = Builder.write_to_path('/tmp/example_payload')
    builder.embed_fuselage_runtime()
    builder.embed_resource_bundle(bundle)

The output is a zipfile that can be executed by python. On linux and OSX it can even be executed directly::

    /tmp/example_payload


Dependencies between resources
==============================

Resources are always applied in the order they are listed in the resource bundle. But if you want to express relationships between steps (for example, you want to run a command after updating a checkout) then you can use the ``watches`` argument.


For example::

    bundle.add(Checkout(
        name="/usr/local/src/mycheckout",
        repository="git://github.com/example/example_project",
    ))

    bundle.add(Execute(
        name="install-requirements",
        command="/var/sites/myapp/bin/pip install -r /usr/local/src/mycheckout/requirements.txt",
        watches=['/usr/local/src/mycheckout'],
    ))

When the ``Checkout`` step pulls in a change from a repository, the ``Execute`` resource will be applied.

You can do the same for monitoring file changes too::

    bundle.add(File(
        name="/etc/apache2/security.conf",
        source="apache2/security.conf",
    ))

    bundle.add(Execute(
        name="restart-apache",
        command="apache2ctl graceful",
        watches=['/etc/apache2/security.conf'],
    ))

Sometimes you can't use ``File`` (perhaps ``buildout`` or ``maven`` or similar generates a config file for you), but you still want to trigger a command when a file changes during deployment::

    bundle.add(Execute(
        name="buildout",
        command="buildout -c production.cfg",
        changes=['/var/sites/mybuildout/parts/apache.cfg'],
    ))

    bundle.add(Execute(
        name="restart-apache",
        command="apache2ctl graceful",
        watches=['/var/sites/mybuildout/parts/apache.cfg'],
    ))

This declares that the ``buildout`` step might change ``/var/sites/mybuildout/parts/apache.cfg``). Subsequent steps can then subscribe to this file as though it was an ordinary ``File`` resource.

All of these examples use a trigger system. When a trigger has been set fuselage will remember it between invocations. Consider the following example::

    bundle.add(File(
        name="/etc/apache2/sites-enabled/mydemosite",
    ))

    bundle.add(File(
        name="/var/local/tmp/this/paths/parent/dont/exist",
    ))

    bundle.add(Execute(
        name="restart-apache2",
        command="/etc/init.d/apache2 restart",
        watches=['/etc/apache2/sites-enabled/mydemosite'],
    ))

By inspection we can tell the 2nd step will fail, so will fuselage restart apache when we've fixed the bug? Yes:

 * On the first run, fuselage will create the file and because a change occurred it will set a trigger for any resources that have a ``watches`` against it. This will be persisted in ``/var/lib/yaybu/event.json`` immediately.
 * It will fail to create a Directory and stop processing changes.
 * A human will correct the configuration and re-run it
 * On the 2nd run it will check the file exists with the correct permissions and make no changes
 * It will create the directory.
 * Before running the restart it will check ``event.json`` to see if it is triggered or not.
 * It will run the restart
 * The trigger will be immediately removed from ``event.json``.

This means that the restart step will always execute when the file changes, even if an intermediate step fails and the process has to be repeated. If the restart fails then fuselage will try again the next time it is run.
