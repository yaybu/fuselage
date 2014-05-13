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

from fuselage import error, resources, provider
from fuselage.changes import ShellCommand


class Execute(provider.Provider):

    policies = (resources.execute.ExecutePolicy,)

    def apply(self):
        creates = self.resource.creates
        if creates and os.path.exists(creates):
            self.logger.debug("%r exists, not executing" % (self.resource.creates,))
            return False

        touch = self.resource.touch
        if touch and os.path.exists(touch):
            self.logger.debug("%r exists, not executing" % (self.resource.touch,))
            return False

        unless = self.resource.unless
        if unless:
            try:
                if self.transport.execute(unless,
                                          user=self.resource.user.as_string,
                                          cwd=self.resource.cwd,
                                          )[0] == 0:
                    return False

            except error.InvalidUser as exc:
                # If a simulation and user missing then we can run our 'unless'
                # guard. We bail out with True so that Yaybu treates the
                # resource as applied.
                self.raise_or_log(exc)

            except error.InvalidGroup as exc:
                # If a simulation and group missing then we can run our 'unless'
                # guard. We bail out with True so that Yaybu treates the
                # resource as applied.
                self.raise_or_log(exc)

        command = self.resource.command
        if command:
            commands = [self.resource.command]
        else:
            commands = self.resource.commands

        for command in commands:
            try:
                self.change(ShellCommand(command,
                                         cwd=self.resource.cwd or None,
                                         env=self.resource.environment or None,
                                         user=self.resource.user or None,
                                         group=self.resource.group or None,
                                         umask=self.resource.umask,
                                         ))
            except error.SystemError as exc:
                if exc.returncode != self.resource.returncode:
                    raise error.CommandError(
                        "%s failed with return code %d" % (self.resource, exc.returncode))

        if self.resource.touch:
            self.change(ShellCommand(["touch", self.resource.touch]))

        return True
