=======
Contrib
=======

The ``fabric.contrib`` module contains examples showing how to integrate fuselage with other tools and libraries such as fabric and libcloud.


Fabric
======

The ``fuselage`` module comes with fabric integration. This is simple a decorator that allows you to simple ``yield`` resources and apply them to any hosts fabric can connect to.

For example in your ``fabfile.py`` you might write::

    from fuselage.contrib.fabric import blueprint
    from fuselage.resources import *

    @blueprint
    def deploy():
        """ Deploy configuration to app server cluster """
        yield File(
            name='/tmp/some-thing'
        )
        yield Package(name="apache2")

This task will show up in your fabric task list like any other::

    # fab -l
    Available commands:

        deploy  Deploy configuration to app server cluster


You can run this against multiple computers::

    # fab -H server1,server2 app_server


Libcloud
========

The libcloud compute API exposes simple deployment functionality via the ``deploy_node`` method. This method starts a compute node and runs one or more ``Deployment`` objects against it. The fuselage contrib module provides ``FuselageDeployment``.

 To create a node at Brightbox and deploy Apache on it you could write something like this::

    from fuselage.contrib.libcloud import FuselageDeployment
    from fuselage.resources import *

    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver

    Driver = get_driver(Provider.BRIGHTBOX)
    driver = Driver('my-client-id', 'my-client-secret')

    images = conn.list_images()
    sizes = conn.list_sizes()

    step = FuselageDeployment(resources=[
        Package(name='apache2'),
        File(
            name='/etc/apache2/sites-enabled/default',
            contents='<VirtualHost>...snip...',
        ),
        Execute(
            name='restart-apache',
            command='apache2ctl graceful',
            watches=['/etc/apache2/sites-enabled/default']
        ),
    ])

    node = conn.deploy_node(
        name='test',
        image=images[0],
        size=sizes[0],
        deploy=step
    )


Vagrant
=======

The easiest way to use fuselage with vagrant is via the `vagrant-fabric`<https://github.com/wutali/vagrant-fabric>_.

You will need to install Virtualbox and Vagrant. Then you can install the ``vagrant-fabric`` plugin::

    vagrant-plugin install vagrant-fabric

You can set up a ``Vagrantfile`` in your project that looks like this::

    # -*- mode: ruby -*-
    # vi: set ft=ruby :

    #Vagrant.require_plugin "vagrant-fabric"

    # Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
    VAGRANTFILE_API_VERSION = "2"

    Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
        config.vm.box = "precise64"
        config.vm.provision :fabric do |fabric|
            fabric.fabfile_path = "./fabfile.py"
            fabric.tasks = ["deploy", ]
        end
    end

You can then run ``vagrant up`` to spin up a new Ubuntu Precise VM and run your
fuselage enabled ``deploy`` task.
