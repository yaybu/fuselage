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

import os
import difflib
import string

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


class EnsureFile(base.Change):

    """ Apply a content change to a file in a managed way. Simulation mode is
    catered for. Additionally the minimum changes required to the contents are
    applied, and logs of the changes made are recorded. """

    def __init__(self, filename, contents, user, group, mode):
        self.filename = filename
        self.current = ""
        self.contents = contents
        self.user = user
        self.group = group
        self.mode = mode
        self.changed = False
        self.renderer = None

    def empty_file(self, context):
        """ Write an empty file """
        exists = os.path.exists(self.filename)
        if not exists:
            context.logger.debug("Creating empty file %r" % self.filename)
            context.change(ShellCommand(["touch", self.filename]))
            self.changed = True
        else:
            st = os.stat(self.filename)
            if st.st_size != 0:
                context.logger.debug("Emptying file %r" % self.filename)
                self.renderer.empty_file(self.filename)
                context.change(
                    ShellCommand(["cp", "/dev/null", self.filename]))
                self.changed = True
            else:
                context.logger.debug("Not changing empty file %r" % self.filename)

    def overwrite_existing_file(self, context):
        """ Change the content of an existing file """
        with open(self.filename, "r") as fp:
            self.current = fp.read()
        if self.current != self.contents:
            context.logger.debug("Changing existing file %r" % self.filename)
            # self.renderer.changed_file(
            #     self.filename, self.current, self.contents, self.sensitive)
            if not context.simulate:
                with open(self.filename, "w") as fp:
                    fp.write(self.contents)
            self.changed = True
        else:
            context.logger.debug("Not changing content of file %r" % self.filename)

    def write_new_file(self, context):
        """ Write contents to a new file. """
        context.logger.debug("Writing new file %r" % self.filename)
        if not context.simulate:
            with open(self.filename, "w") as fp:
                fp.write(self.contents)
        self.changed = True

    def write_file(self, context):
        """ Write to either an existing or new file """
        if os.path.exists(self.filename):
            self.overwrite_existing_file(context)
        else:
            self.write_new_file(context)

    def apply(self, context):
        """ Apply the changes necessary to the file contents. """
        if self.contents is None:
            self.empty_file(context)
        else:
            self.write_file(context)

        ac = AttributeChanger(self.filename, self.user, self.group, self.mode)
        context.change(ac)
        self.changed = self.changed or ac.changed
        return self


class FileChangeTextRenderer(object):
    renderer_for = EnsureFile

    def empty_file(self, filename):
        self.logger.notice("Emptied file %s" % filename)

    def new_file(self, filename, contents, sensitive):
        self.logger.notice("Writing new file '%s'" % filename)
        if not sensitive:
            self.diff("", contents)

    def changed_file(self, filename, previous, replacement, sensitive):
        self.logger.notice("Changed file %s" % filename)
        if not sensitive:
            self.diff(previous, replacement)

    def diff(self, previous, replacement):
        if not binary_buffers(previous, replacement):
            diff = "".join(difflib.unified_diff(
                previous.splitlines(1), replacement.splitlines(1)))
            for l in diff.splitlines():
                self.logger.info("    %s" % l)
        else:
            self.logger.notice("Binary contents; not showing delta")
