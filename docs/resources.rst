.. _resources:

=========
Resources
=========

This section describes the core resources you can use to describe your server configuration.

Line
====

Ensure that a line is present or missing from a file.

For example, this will ensure that selinux is disabled::

    Line(
        name="/etc/selinux/config",
        match=r"^SELINUX",
        replace="SELINUX=disabled",
    )

The available parameters are:

``name``
    The full path to the file to perform an operation on.
``match``
    The python regular expression to match the line to be updated.
``replace``
    The text to insert at the point the expression matches (otherwise at the end of the file).


File
====

A provider for this resource will create or amend an existing file to the
provided specification.

For example, the following will create the /etc/hosts file based on a static
local file::

    File(
        name="/etc/hosts",
        owner="root",
        group="root",
        mode=0o644,
        source="my_hosts_file",
    )

The available parameters are:

``name``
    The full path to the file this resource represents.
``owner``
    A unix username or UID who will own created objects. An owner that
    begins with a digit will be interpreted as a UID, otherwise it will be
    looked up using the python 'pwd' module.
``group``
    A unix group or GID who will own created objects. A group that begins
    with a digit will be interpreted as a GID, otherwise it will be looked up
    using the python 'grp' module.
``mode``
    A mode representation as an octal. This can begin with leading zeros if
    you like, but this is not required. DO NOT use yaml Octal representation
    (0o666), this will NOT work.
``source``
    An optional file that is rendered into ``name`` on the target. Fuselage
    searches the searchpath to find it.
``contents``
    The arguments passed to the renderer.


Directory
=========

A directory on disk. Directories have limited metadata, so this resource is
quite limited.

For example::

    Directory(
        name="/var/local/data",
        owner="root",
        group="root",
        mode=0o755,
    )

The available parameters are:

``name``
    The full path to the directory on disk
``owner``
    The unix username who should own this directory, by default this is 'root'
``group``
    The unix group who should own this directory, by default this is 'root'
``mode``
    The octal mode that represents this directory's permissions, by default
    this is '755'.
``parents``
    Create parent directories as needed, using the same ownership and
    permissions, this is False by default.


Link
====

A resource representing a symbolic link. The link will be from `name` to `to`.
If you specify owner, group and/or mode then these settings will be applied to
the link itself, not to the object linked to.

For example::

    Link(
        name="/etc/init.d/exampled",
        to="/usr/local/example/sbin/exampled",
        owner="root",
        group="root",
    )

The available parameters are:

``name``
    The name of the file this resource represents.
``owner``
    A unix username or UID who will own created objects. An owner that
    begins with a digit will be interpreted as a UID, otherwise it will be
    looked up using the python 'pwd' module.
``group``
    A unix group or GID who will own created objects. A group that begins
    with a digit will be interpreted as a GID, otherwise it will be looked up
    using the python 'grp' module.
``to``
    The pathname to which to link the symlink. Dangling symlinks ARE
    considered errors in Fuselage.


Execute
=======

Execute a command. This command *is* executed in a shell subprocess.

For example::

    Execute(
        name="add-apt-key",
        command="apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 0x000000"
    )

The available parameters are:

``name``
    The name of this resource. This should be unique and descriptive, and
    is used so that resources can reference each other.
``command``
    If you wish to run a single command, then this is the command.
``commands``
    If you wish to run multiple commands, provide a list
``cwd``
    The current working directory in which to execute the command.
``environment``
    The environment to provide to the command, for example::

        Execute(
            name="example",
            command="echo $FOO",
            environment={"FOO": "bar"},
        )
``returncode``
    The expected return code from the command, defaulting to 0. If the
    command does not return this return code then the resource is considered
    to be in error.
``user``
    The user to execute the command as.
``group``
    The group to execute the command as.
``umask``
    The umask to use when executing this command
``unless``
    A command to run to determine is this execute should be actioned
``creates``
    The full path to a file that execution of this command creates. This
    is used like a "touch test" in a Makefile. If this file exists then the
    execute command will NOT be executed.
``touch``
    The full path to a file that fuselage will touch once this command has
    completed successfully. This is used like a "touch test" in a Makefile. If
    this file exists then the execute command will NOT be executed.


Checkout
========

This represents a "working copy" from a Source Code Management system.
This could be provided by, for example, Subversion or Git remote
repositories.

Note that this is '*a* checkout', not 'to checkout'. This represents the
resource itself on disk. If you change the details of the working copy
(for example changing the branch) the provider will execute appropriate
commands (such as ``svn switch``) to take the resource to the desired state.

For example::

    Checkout(
        name="/usr/src/myapp",
        repository="https://github.com/myusername/myapp",
        scm="git",
    )

The available parameters are:

``name``
    The full path to the working copy on disk.
``repository``
    The identifier for the repository - this could be an http url for
    subversion or a git url for git, for example.
``branch``
    The name of a branch to check out, if required.
``tag``
    The name of a tag to check out, if required.
``revision``
    The revision to check out or move to.
``scm``
    The source control management system to use, e.g. subversion, git.
``scm_username``
    The username for the remote repository
``scm_password``
    The password for the remote repository.
``user``
    The user to perform actions as, and who will own the resulting files.
    The default is root.
``group``
    The group to perform actions as. The default is to use the primary group of
    ``user``.
``mode``
    A mode representation as an octal. This can begin with leading zeros if
    you like, but this is not required. DO NOT use yaml Octal representation
    (0o666), this will NOT work.


Package
=======

Represents an operating system package, installed and managed via the
OS package management system. For example, to ensure these three packages
are installed::

    Package(
        name="apache2",
    )

The available parameters are:

``name``
    The name of the package. This can be a single package or a list can be
    supplied.
``version``
    The version of the package, if only a single package is specified and
    the appropriate provider supports it (the Apt provider does not support
    it).
``purge``
    When removing a package, whether to purge it or not.

When installing a package ``apt-get`` may give a ``404`` error if your local
apt cache is stale. If Fuselage thinks this might be the cause it will ``apt-get
update`` and retry before giving up.


User
====

A resource representing a UNIX user in the password database. The underlying
implementation currently uses the "useradd" and "usermod" commands to implement
this resource.

This resource can be used to create, change or delete UNIX users.

For example::

    User(
        name="django",
        fullname="Django Software Owner",
        home="/var/local/django",
        system=True,
        disabled_password=True,
    )

The available parameters are:

``name``
    The username this resource represents.
``password``
    The encrypted password, as returned by crypt(3). You should make sure
    this password respects the system's password policy.
``fullname``
    The comment field for the password file - generally used for the user's
    full name.
``home``
    The full path to the user's home directory.
``uid``
    The user identifier for the user. This must be a non-negative integer.
``gid``
    The group identifier for the user. This must be a non-negative integer.
``group``
    The primary group for the user, if you wish to specify it by name.
``groups``
    A list of supplementary groups that the user should be a member of.
``append``
    A boolean that sets how to apply the groups a user is in. If true then
    fuselage will add the user to groups as needed but will not remove a user from
    a group. If false then fuselage will replace all groups the user is a member
    of. Thus if a process outside of fuselage adds you to a group, the next
    deployment would remove you again.
``system``
    A boolean representing whether this user is a system user or not. This only
    takes effect on creation - a user cannot be changed into a system user once
    created without deleting and recreating the user.
``shell``
    The full path to the shell to use.
``disabled_password``
    A boolean for whether the password is locked for this account.
``disabled_login``
    A boolean for whether this entire account is locked or not.


Group
=====

A resource representing a unix group stored in the /etc/group file.
``groupadd`` and ``groupmod`` are used to actually make modifications.

For example::

    Group(
        name="zope",
        system=True,
    )

The available parameters are:

``name``
    The name of the unix group.
``gid``
    The group ID associated with the group. If this is not specified one will
    be chosen.
``system``
    Whether or not this is a system group - i.e. the new group id will be
    taken from the system group id list.
``password``
    The password for the group, if required


Service
=======

This represents service startup and shutdown via an init daemon.

The available parameters are:

``name``
    A unique name representing an initd service. This would normally match the
    name as it appears in /etc/init.d.
``priority``
    Priority of the service within the boot order. This attribute will have no
    effect when using a dependency or event based init.d subsystem like upstart
    or systemd.
``start``
    A command that when executed will start the service. If not provided, the
    provider will use the default service start invocation for the init.d
    system in use.
``stop``
    A command that when executed will start the service. If not provided, the
    provider will use the default service stop invocation for the init.d system
    in use.
``restart``
    A command that when executed will restart the service. If not provided, the
    provider will use the default service restart invocation for the init.d
    system in use. If it is not possible to automatically determine if the restart
    script is avilable the service will be stopped and started instead.
``reconfig``
    A command that when executed will make the service reload its
    configuration file.
``running``
    A comamnd to execute to determine if a service is running. Should have an
    exit code of 0 for success.
``pidfile``
    Where the service creates its pid file. This can be provided instead of
    ``running``  as an alternative way of checking if a service is running or not.
