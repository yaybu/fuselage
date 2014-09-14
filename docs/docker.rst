==================
Docker integration
==================

Our approach for Docker integration is to generate an executable payload, and
use the Docker service and a Dockerfile to build a container.


Using with fabric
=================

fuselage ships with a python decorator that turns a python function that yields
fuselage resources into a fabric task that builds containers::

    from fuselage.fabric import docker_container
    from fuselage.resources import *


    @docker_container(tag='myproject:appserver', ports=[8000], cmd=['python', '-m', 'SimpleHTTPServer'])
    def app_server(bundle, **kwargs):
        yield Package(name="python")
        yield File(
            name="/index.html",
            contents="HELLO WORLD!",
        )

You can build this with::

    fab app_server

Once the container is created you can run it like any other::

    docker run -t -i -p 8000 myproject:appserver

If you aren't familiar with Docker, ``-t`` and ``-i`` will run the task
interactively and in the foreground. ``-p`` maps port 8000 in the container to
an ephemeral port on the host.

The decorator takes the following arguments (which map to Dockerfile instructions and docker build arguments):

``from_image``
    This maps the the Dockerfile ``FROM`` instruction. It sets the container to
    base your new container on. For example, specify ``ubuntu:14.04`` to build an
    Ubuntu Trusty container.
``tag``
    The name of your container. If this isn't specified your container won't be
    named, but you'll still be able to refer to it by it's image ID.
``env``
    A python dictionary. This maps to multiple Dockerfile ``ENV`` instructions.
    These environment variables are set in the build environment and the
    runtime.
``volumes``
    A python list. Maps to the Dockerfile ``VOLUMES`` instruction. A list of
    directories to share between containers or with the host. Typically used to
    store data outside of a container, allowing you to upgrade your application by
    replacing it with a new container.
``ports``
    A python list. Maps to the Dockerfile ``EXPOSE`` instruction. These are all
    the ports that you hope to access from outside the container.
``cmd``
    A python list. This is the default command to run when your container is
    run. You can override this when starting your container.
``maintainer``
    A string. This maps to the ``MAINTAINER`` Dockerfile instruction. The name
    of the person to come and bother when there is a problem with the container.

As well as specifying these in your ``fabfile.py`` you can override them when
running the fabric task::

    fab app_server:tag=mytag


Building containers programatically
===================================

You first of all need to build a resource bundle::

    from fuselage import bundle
    from fuselage.resources import *

    b = bundle.ResourceBundle()
    b.add(Package(name="python"))

The create a ``DockerBuilder``, configure your build and execute it::

    from fuselage.docker import DockerBuilder
    d = DockerBuilder(
        b,
        from_image='ubuntu:14.04',
        tag='test-image',
        )
    list(d.build())
