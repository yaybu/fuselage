# Copyright 2011-2014 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from fuselage.resource import Resource
from fuselage.policy import Policy, Present, XOR
from fuselage.utils import simple_str
from fuselage.argument import (
    FullPath,
    String,
    Integer,
    Octal,
    Dict,
    List,
)
from fuselage.defaults import get_default_user, get_default_group


class Execute(Resource):

    """ Execute a command. This command is not executed in a shell - if you
    want a shell, run it (for example bash -c).

    For example::

        Execute:
          name: core_packages_apt_key
          command: apt-key adv --keyserver keyserver.ubuntu.com --recv-keys {{source.key}}

    A much more complex example. This shows executing a command if a checkout synchronises::

        Execute.foreach bi in {{flavour.base_images}}:
          name: base-image-{{bi}}
          policy:
              apply:
                  when: sync
                  on: /var/local/checkouts/ci
          command: ./vmbuilder-{{bi}}
          cwd: /var/local/checkouts/ci
          user: root

    """

    @property
    def implicit_id(self):
        implicit_id = super(Execute, self).implicit_id
        if not implicit_id:
            if self.command:
                implicit_id = simple_str(self.command)
            elif self.commands:
                implicit_id = simple_str("; ".join(self.commands))
        return implicit_id

    name = String()
    """ The name of this resource. This should be unique and descriptive, and
    is used so that resources can reference each other. """

    command = String()
    """ If you wish to run a single command, then this is the command. """

    commands = List()
    """ If you wish to run multiple commands, provide a list """

    cwd = FullPath(default='/')
    """ The current working directory in which to execute the command. """

    env = Dict()
    """

    The environment to provide to the command, for example::

        Execute:
            name: example
            command: echo $FOO
            environment:
                FOO: bar
    """

    returncode = Integer(default=0)
    """ The expected return code from the command, defaulting to 0. If the
    command does not return this return code then the resource is considered
    to be in error. """

    user = String(default=lambda r: get_default_user())
    """ The user to execute the command as.
    """

    group = String(default=lambda r: get_default_group(r.user))
    """ The group to execute the command as.
    """

    umask = Octal(default=0o022)
    """ The umask to use when executing this command """

    unless = String(default="")
    """ A command to run to determine is this execute should be actioned
    """

    creates = FullPath()
    """ The full path to a file that execution of this command creates. This
    is used like a "touch test" in a Makefile. If this file exists then the
    execute command will NOT be executed. """

    touch = FullPath()
    """ The full path to a file that yaybu will touch once this command has
    completed successfully. This is used like a "touch test" in a Makefile. If
    this file exists then the execute command will NOT be executed. """


class ExecutePolicy(Policy):

    """ Execute the the command or commands provided.

    If user or group attributes are provided the command will be run using sudo."""

    resource = Execute
    name = "execute"
    default = True
    signature = (
        XOR(Present("command"), Present("commands")),
    )
