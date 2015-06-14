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

""" Resources for handling the creation and removal of files. These deal with
both the metadata associated with the file (for example owner and permission)
and the contents of the files themselves. """

from fuselage.resource import Resource
from fuselage.policy import (
    Policy,
    Absent,
    Present,
    NAND,
)

from fuselage.argument import (
    FullPath,
    String,
    Octal,
    File,
    Boolean,
)
from fuselage.defaults import get_default_user, get_default_group


class File(Resource):

    """ A provider for this resource will create or amend an existing file to
    the provided specification.

    For example, the following will create the /etc/hosts file based on a static local file::

        File:
          name: /etc/hosts
          owner: root
          group: root
          mode: 644
          static: my_hosts_file

    The following will create a file using a jinja2 template, and will back up
    the old version of the file if necessary::

        File:
          name: /etc/email_addresses
          owner: root
          group: root
          mode: 644
          template: email_addresses.j2
          template_args:
              foo: foo@example.com
              bar: bar@example.com
          backup: /etc/email_addresses.{year}-{month}-{day}

    """

    name = FullPath()
    """The full path to the file this resource represents."""

    owner = String(default=lambda r: get_default_user())
    """A unix username or UID who will own created objects. An owner that
    begins with a digit will be interpreted as a UID, otherwise it will be
    looked up using the python 'pwd' module."""

    group = String(default=lambda r: get_default_group(r.owner))
    """A unix group or GID who will own created objects. A group that begins
    with a digit will be interpreted as a GID, otherwise it will be looked up
    using the python 'grp' module."""

    mode = Octal(default=0o644)
    """A mode representation as an octal. This can begin with leading zeros if
    you like, but this is not required. DO NOT use yaml Octal representation
    (0o666), this will NOT work."""

    contents = String(default=None)
    """ A complete string to write into a file """

    source = File()
    """A file that will be applied to this resource. """

    sensitive = Boolean(default=False)

    def hash(self):
        from fuselage import platform
        try:
            return platform.stat(self.name).st_mtime
        except OSError:
            return 0


class FileApplyPolicy(Policy):

    """ Create a file and populate it's contents if required.

    You must provide a name.

    You may provide one of template, static, or encrypted to act as a file source.
    """

    resource = File
    name = "apply"
    default = True
    signature = (
        Present("name"),
        NAND(
            Present("contents"),
            Present("source")
        )
    )


class FileRemovePolicy(Policy):

    """ Delete a file if it exists. You should only provide the name in this
    case. """

    resource = File
    name = "remove"
    default = False
    signature = (Present("name"),
                 Absent("owner"),
                 Absent("group"),
                 Absent("mode"),
                 )


class FileWatchedPolicy(Policy):

    """ Watches a file to see if it changes when a resource a file.

    This policy is used internally and shouldn't be used directly.
    """

    resource = File
    name = "watched"
    default = False
    signature = FileRemovePolicy.signature
