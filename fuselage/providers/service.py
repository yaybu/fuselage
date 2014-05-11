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

from fuselage import provider
from fuselage import error
from fuselage import resources
from fuselage.changes import ShellCommand


class _ServiceMixin(object):
    features = ["restart", ]

    def status(self, context):
        if self.resource.running:
            rc, stdout, stderr = context.transport.execute(self.resource.running)
            if rc == 0:
                return "running"
            else:
                return "not-running"

        if not self.resource.pidfile:
            return "unknown"

        if not os.path.exists(self.resource.pidfile):
            return "not-running"

        with open(self.resource.pidfile, "r") as fp:
            try:
                pid = int(fp.read().strip())
            except:
                return "unknown"

        # if os.path.exists("/proc/%s" % pid):
        #     return "running"

        try:
            os.kill(0, pid)
            return "running"
        except OSError:
            return "not-running"

    def do(self, context, action):
        try:
            context.change(ShellCommand(self.get_command(action)))
        except error.SystemError as exc:
            raise error.CommandError(
                "%s failed with return code %d" % (action, exc.returncode))

    def ensure_enabled(self, context):
        pass

    def ensure_disabled(self, context):
        pass

    def get_command(self, action):
        return (
            shlex.split(
                getattr(
                    self.resource,
                    action).as_string(
                ).encode(
                    "UTF-8"))
        )


class Start(_ServiceMixin, provider.Provider):

    policies = (resources.service.ServiceStartPolicy,)

    def apply(self, context, output):
        changed = self.ensure_enabled(context)

        if self.status(context) == "running":
            return changed

        self.do(context, "start")

        return True


class Stop(_ServiceMixin, provider.Provider):

    policies = (resources.service.ServiceStopPolicy,)

    def apply(self, context, output):
        changed = self.ensure_disabled(context)

        if self.status(context) == "not-running":
            return changed

        self.do(context, "stop")

        return True


class Restart(_ServiceMixin, provider.Provider):

    policies = (resources.service.ServiceRestartPolicy,)

    def apply(self, context, output):
        self.ensure_enabled(context)

        if self.status(context) == "not-running":
            self.do(context, "start")
            return True

        if "restart" in self.features:
            self.do(context, "restart")
        else:
            self.do(context, "stop")
            self.do(context, "start")

        return True
