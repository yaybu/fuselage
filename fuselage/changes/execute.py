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

import six
import os
import shlex

from fuselage import error, shell
from fuselage.changes import base


class ShellCommand(base.Change):

    """ Execute and log a change """

    changed = True

    def __init__(self, command, shell=None, stdin=None, cwd=None, env=None, user="root", group=None, umask=None, expected=0):
        self.command = command
        self.shell = shell
        self.stdin = stdin
        self.cwd = cwd

        self.env = {
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        }
        if env:
            self.env.update(env)

        self.user = user
        self.group = group
        self.umask = umask
        self.expected = expected

    def _tounicode(self, l):
        """ Ensure all elements of the list are unicode """
        def uni(x):
            if isinstance(x, type(u"")):
                return x
            return unicode(x, "utf-8")
        return map(uni, l)

    def command_exists(self, command):
        if command[0].startswith("./"):
            if len(command[0]) <= 2:
                return False
            return os.path.exists(os.path.join(self.cwd, command[0][2:]))

        elif command[0].startswith("/"):
            return os.path.exists(command[0])

        for path in self.env["PATH"].split(os.pathsep):
            if os.path.exists(os.path.join(path, command[0])):
                return True

    def apply(self, ctx):
        if isinstance(self.command, list):
            logas = command = self.command
        elif isinstance(self.command, six.string_types):
            logas = command = shlex.split(self.command.encode("UTF-8"))

        command = self._tounicode(command)
        logas = self._tounicode(logas)

        if not self.command_exists(command):
            ctx.raise_or_log(error.BinaryMissing("Command '%s' not found" % command[0]))
            self.returncode = 0
            self.stdout = ""
            self.stderr = ""
            return

        if ctx.simulate:
            self.returncode = 0
            self.stdout = ""
            self.stderr = ""
            return

        p = shell.Process(
            command=command,
            user=self.user,
            group=self.group,
            umask=self.umask,
            env=self.env,
        )

        p.attach_callback(ctx.changelog.info)
        self.stdout, self.stderr = p.communicate(stdin=self.stdin)
        self.returncode = p.wait()

        if self.expected is not None and self.returncode != self.expected:
            raise error.SystemError(self.returncode, self.stdout, self.stderr)


def _handle_slash_r(line):
    line = line.rstrip("\r")
    if "\r" in line:
        line = line.rsplit("\r", 1)[1]
    return line


class ShellTextRenderer(object):

    """ Render a ShellCommand. """

    renderer_for = ShellCommand

    stdout_buffer = ""
    stderr_buffer = ""

    def command(self, command):
        self.logger.notice(u"# " + u" ".join(command))

    def output(self, returncode):
        if self.verbose >= 1 and returncode != 0 and not self.inert:
            self.logger.notice("returned %s", returncode)

    def stdout(self, data):
        if self.verbose >= 2:
            data = self.stdout_buffer + data
            if "\n" not in data:
                self.stdout_buffer = data
                return
            data, self.stdout_buffer = data.rsplit("\n", 1)
            for line in data.split("\n"):
                self.logger.info(_handle_slash_r(line))

    def stderr(self, data):
        if self.verbose >= 1:
            data = self.stderr_buffer + data
            if "\n" not in data:
                self.stdout_buffer = data
                return
            data, self.stderr_buffer = data.rsplit("\n", 1)
            for line in data.split("\n"):
                self.logger.info(_handle_slash_r(line))

    def flush(self):
        if self.stdout_buffer:
            self.logger.info(_handle_slash_r(self.stdout_buffer))
        if self.stderr_buffer:
            self.logger.info(_handle_slash_r(self.stderr_buffer))

    def exception(self, exception):
        self.logger.notice("Exception: %r" % exception)
