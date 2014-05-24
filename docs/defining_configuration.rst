======================
Defining configuration
======================


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
        watches=['/etc/apache2/security.conf'],
    ))

This declares that the ``buildout`` step might change a ``File`` (the ``apache.cfg``). Subsequent step can then subscribe to ``File[/var/sites/mybuildout/parts/apache.cfg]`` as though it was an ordinary file.

All of these examples use a trigger system. When a trigger has been set fuselage will remember it between invocations. Consider the following example::

    resources:
      - File:
          name: /etc/apache2/sites-enabled/mydemosite

      - Directory:
          name: /var/local/tmp/this/paths/parent/dont/exist

      - Execute:
          name: restart-apache2
          command: /etc/init.d/apache2 restart
          policy:
              execute:
                  when: apply
                  on: File[/etc/apache2/sites-enabled/mydemosite]

When it is run it will create a file in the ``/etc/apache2/sites-enabled`` folder. Fuselage knows that the ``Execute[restart-apache2]`` step must be run later. It will record a trigger for the ``Execute`` statement in ``/var/run/yaybu/``. If the ``Directory[]`` step fails and fuselage terminates then the next time fuselage is execute it will instruct you to use the ``--resume`` or ``--no-resume`` command line option. If you ``--resume`` it will remember that it needs to restart apache2. If you choose ``--no-resume`` it will not remember, and apache will not be restarted.
