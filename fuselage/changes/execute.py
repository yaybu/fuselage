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

from fuselage import error, platform
from fuselage.changes import base
from fuselage.utils import force_str


class ShellCommand(base.Change):

    """ Execute and log a change """

    changed = True

    def __init__(self, command, shell=None, stdin=None, cwd=None, env=None, user="root", group=None, umask=None, expected=0, logas=None):
        if isinstance(command, list):
            self.command = command
        elif isinstance(command, six.string_types):
            self.command = shlex.split(command)
        else:
            raise RuntimeError("'command' must be a list or string")

        # Commands can be logged differently to what is executed, so that passwords aren't revealed
        if logas:
            if isinstance(logas, six.string_types):
                self.logas = shlex.split(self.command)
            else:
                self.logas = logas
        else:
            self.logas = self.command

        self.stdin = stdin
        self.cwd = cwd

        self.env = {}
        if platform.platform == "win32":
            self.env.update({
                "PATH": os.environ.get("PATH", ""),
            })
        else:
            self.env.update({
                "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            })
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
            return x.encode("utf-8")
        return list(map(uni, l))

    def command_exists(self, command):
        if command[0].startswith("./"):
            if len(command[0]) <= 2:
                return False
            return platform.exists(os.path.join(self.cwd, command[0][2:]))

        elif command[0].startswith("/"):
            return platform.exists(command[0])

        for path in self.env["PATH"].split(platform.pathsep):
            if platform.exists(os.path.join(path, command[0])):
                return True

    def apply(self, ctx):
        command, logas = self.command, self.logas

        ctx.changelog.critical('# ' + ' '.join([force_str(l) for l in logas]))

        if not self.command_exists(command):
            ctx.raise_or_log(error.BinaryMissing("Command '%s' not found" % command[0]))

        if platform.getpwnam and self.user:
            try:
                platform.getpwnam(self.user)
            except KeyError:
                ctx.raise_or_log(error.InvalidUser("User '%s' not found" % self.user))

        if platform.getgrnam and self.group:
            try:
                platform.getgrnam(self.group)
            except KeyError:
                ctx.raise_or_log(error.InvalidGroup("User '%s' not found" % self.group))

        if self.cwd:
            if not platform.isdir(self.cwd):
                ctx.raise_or_log(error.PathComponentNotDirectory("%r not a directory" % self.cwd))

        if ctx.simulate:
            self.returncode = 0
            self.stdout = ""
            self.stderr = ""
            return

        self.stdout, self.stderr = platform.check_call(
            command=command,
            user=self.user,
            group=self.group,
            umask=self.umask,
            env=self.env,
            cwd=self.cwd,
            expected=self.expected,
            logger=ctx.changelog,
        )
