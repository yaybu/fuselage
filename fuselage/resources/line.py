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

import os

from fuselage.resource import Resource
from fuselage.policy import (
    Policy,
    Present,
)

from fuselage.argument import (
    FullPath,
    String,
    Boolean,
)
from fuselage.utils import simple_str, force_str


class Line(Resource):

    """
    Ensure that a line is present or missing from a file.

    For example, this will ensure that selinux is disabled::

        Line(
            name="/etc/selinux/config",
            match=r"^SELINUX",
            replace="SELINUX=disabled",
        )
    """

    @property
    def implicit_id(self):
        return force_str(self.name) + ":" + simple_str(self.match)

    name = FullPath()
    """ The full path to the file to perform an operation on. """

    line = String(default="")
    """ The text to insert at the point the expression matches (otherwise at the end of the file). """

    match = String(default="")
    """ The python regular expression to match the line to be updated. """

    linesep = String(default=os.linesep)
    """ The delimiter used to mark a line. \\n on posix. """

    sensitive = Boolean(default=False)


class LineApplyPolicy(Policy):

    """ Create a file and populate it's contents if required.

    You must provide a name.

    You may provide one of template, static, or encrypted to act as a file source.
    """

    resource = Line
    name = "apply"
    default = True
    signature = (
        Present("name"),
        Present("line"),
        Present("match"),
    )


class LineRemovePolicy(Policy):

    """
    Ensure lines matching the regular expression are removed from the file.
    """

    resource = Line
    name = "remove"
    signature = (
        Present("name"),
        Present("match"),
    )
