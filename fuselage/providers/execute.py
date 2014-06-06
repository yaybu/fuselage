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

from fuselage import error, resources, provider, platform
from fuselage.changes import ShellCommand


class Execute(provider.Provider):

    policies = (resources.execute.ExecutePolicy,)

    def check_unless(self):
        try:
            platform.check_call(
                command=self.resource.unless,
                user=self.resource.user,
                cwd=self.resource.cwd,
            )

        except error.InvalidUser as exc:
            self.raise_or_log(exc)

        except error.InvalidGroup as exc:
            self.raise_or_log(exc)

        except error.SystemError as exc:
            return True

        return False

    def apply(self):
        creates = self.resource.creates
        if creates and platform.exists(creates):
            self.logger.debug("%r exists, not executing" % (self.resource.creates,))
            return False

        touch = self.resource.touch
        if touch and platform.exists(touch):
            self.logger.debug("%r exists, not executing" % (self.resource.touch,))
            return False

        if self.resource.unless and not self.check_unless():
            self.logger.debug("%r passes, not executing" % (self.resource.unless, ))
            return False

        if self.resource.command:
            commands = [self.resource.command]
        else:
            commands = self.resource.commands

        for command in commands:
            self.change(ShellCommand(
                command=command,
                cwd=self.resource.cwd or None,
                env=self.resource.env or None,
                user=self.resource.user or None,
                group=self.resource.group or None,
                umask=self.resource.umask,
                expected=self.resource.returncode,
            ))

        if self.resource.touch:
            self.change(ShellCommand(["touch", self.resource.touch]))

        return True
