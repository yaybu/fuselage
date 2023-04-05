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

""" Resources dealing with filesystem objects other than files. """

from fuselage.argument import Boolean, FullPath, Octal, String
from fuselage.defaults import get_default_group, get_default_user
from fuselage.policy import Absent, Policy, Present
from fuselage.resource import Resource


class Directory(Resource):

    """A directory on disk. Directories have limited metadata, so this
    resource is quite limited.

    For example::

        Directory:
          name: /var/local/data
          owner: root
          group: root
          mode: 0755

    """

    name = FullPath()
    """ The full path to the directory on disk """

    owner = String(default=lambda r: get_default_user())
    """ The unix username who should own this directory, by default this is 'root' """

    group = String(default=lambda r: get_default_group(r.owner))
    """ The unix group who should own this directory, by default this is 'root' """

    mode = Octal(default=0o755)
    """ The octal mode that represents this directory's permissions, by default this is '755'. """

    parents = Boolean(default=False)
    """ Create parent directories as needed, using the same ownership and
    permissions, this is False by default. """


class DirectoryAppliedPolicy(Policy):

    """Ensure a directory exists and matches the specification provided
    by the resource."""

    resource = Directory
    name = "apply"
    default = True
    signature = (Present("name"),)


class DirectoryRemovedPolicy(Policy):

    """If a directory described by this resource exists then remove it.

    This isn't recursive, if you want to remove a directory and all its contents
    use `remove-recursive`.

    You should only provide the path to the directory when using this policy.
    Other fields are not needed.
    """

    resource = Directory
    name = "remove"
    default = False
    signature = (
        Present("name"),
        Absent("owner"),
        Absent("group"),
        Absent("mode"),
    )


class DirectoryRemovedRecursivePolicy(Policy):

    """If a directory described by this resource exists then remove it and
    its children.

    You should only provide the path to the directory when using this policy.
    Other fields are not needed.
    """

    resource = Directory
    name = "remove-recursive"
    default = False
    signature = (
        Present("name"),
        Absent("owner"),
        Absent("group"),
        Absent("mode"),
    )
