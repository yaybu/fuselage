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

import difflib
import string

from fuselage import platform
from fuselage.changes import base
from .execute import ShellCommand
from .attributes import AttributeChanger


# FIXME: Set mode of file before writing to it


def binary_buffers(*buffers):
    """ Check all of the passed buffers to see if any of them are binary. If
    any of them are binary this will return True. """
    check = lambda buff: len(buff) == sum(
        1 for c in buff if c in string.printable)
    for buff in buffers:
        if buff and not check(buff):
            return True
    return False


class EnsureContents(base.Change):

    """ Apply a content change to a file in a managed way. Simulation mode is
    catered for. Additionally the minimum changes required to the contents are
    applied, and logs of the changes made are recorded. """

    def __init__(self, filename, contents, sensitive=False):
        self.filename = filename
        self.current = ""
        self.contents = contents
        self.changed = False
        self.sensitive = sensitive

    def diff(self, context, note, previous, replacement):
        extra = {}
        if self.sensitive:
            extra['fuselage.diff'] = 'No diff; sensitive file contents'
        elif not binary_buffers(previous, replacement):
            diff = "".join(difflib.unified_diff(previous.splitlines(1), replacement.splitlines(1)))
            extra['fuselage.diff'] = diff
        else:
            extra['fuselage.diff'] = 'No diff; binary files'
        context.changelog.critical(note, extra=extra)

    def empty_file(self, context):
        """ Write an empty file if none exists"""
        if not platform.exists(self.filename):
            context.changelog.debug("Creating empty file %r" % self.filename)
            context.change(ShellCommand(["touch", self.filename]))
            self.changed = True

    def overwrite_existing_file(self, context):
        """ Change the content of an existing file """
        self.current = platform.get(self.filename)
        if self.current != self.contents:
            self.diff(context, "Changing existing file", self.current, self.contents)
            if not context.simulate:
                platform.put(self.filename, self.contents)
            self.changed = True
        else:
            context.logger.debug("Not changing content of file %r" % self.filename)

    def write_new_file(self, context):
        """ Write contents to a new file. """
        self.diff(context, "Writing new file", "", self.contents)
        if not context.simulate:
            platform.put(self.filename, self.contents)
        self.changed = True

    def write_file(self, context):
        """ Write to either an existing or new file """
        if platform.exists(self.filename):
            self.overwrite_existing_file(context)
        else:
            self.write_new_file(context)

    def apply(self, context):
        if self.contents is None:
            self.empty_file(context)
        else:
            self.write_file(context)
        return self.changed


class EnsureFile(base.Change):

    def __init__(self, filename, contents, user, group, mode, sensitive=False):
        self.filename = filename
        self.contents = contents
        self.user = user
        self.group = group
        self.mode = mode
        self.changed = False
        self.sensitive = sensitive

    def apply(self, context):
        """ Apply the changes necessary to the file contents. """
        fc = EnsureContents(self.filename, self.contents, sensitive=self.sensitive)
        context.change(fc)

        ac = AttributeChanger(self.filename, self.user, self.group, self.mode)
        context.change(ac)

        self.changed = fc.changed or ac.changed
        return self
