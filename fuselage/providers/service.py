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
import shlex

from fuselage import provider, error, resources, platform
from fuselage.changes import ShellCommand


class _ServiceMixin(object):
    features = ["restart", ]

    def status(self):
        if self.resource.running:
            rc, stdout, stderr = platform.check_call(self.resource.running)
            if rc == 0:
                return "running"
            else:
                return "not-running"

        if not self.resource.pidfile:
            return "unknown"

        if not platform.exists(self.resource.pidfile):
            return "not-running"

        try:
            pid = int(platform.get(self.resource.pidfile))
        except:
            return "unknown"

        # if platform.exists("/proc/%s" % pid):
        #     return "running"

        try:
            os.kill(0, pid)
            return "running"
        except OSError:
            return "not-running"

    def do(self, action):
        try:
            self.change(ShellCommand(self.get_command(action)))
        except error.SystemError as exc:
            raise error.CommandError(
                "%s failed with return code %d" % (action, exc.returncode))

    def ensure_enabled(self):
        pass

    def ensure_disabled(self):
        pass

    def get_command(self, action):
        return shlex.split(getattr(self.resource, action).encode("utf-8"))


class Start(_ServiceMixin, provider.Provider):

    policies = (resources.service.ServiceStartPolicy,)

    def apply(self, output):
        changed = self.ensure_enabled()

        if self.status() == "running":
            return changed

        self.do("start")

        return True


class Stop(_ServiceMixin, provider.Provider):

    policies = (resources.service.ServiceStopPolicy,)

    def apply(self, output):
        changed = self.ensure_disabled()

        if self.status() == "not-running":
            return changed

        self.do("stop")

        return True


class Restart(_ServiceMixin, provider.Provider):

    policies = (resources.service.ServiceRestartPolicy,)

    def apply(self, output):
        self.ensure_enabled()

        if self.status() == "not-running":
            self.do("start")
            return True

        if "restart" in self.features:
            self.do("restart")
        else:
            self.do("stop")
            self.do("start")

        return True
