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

from fuselage import provider, error, resources, platform
from fuselage.changes import ShellCommand


class _ServiceMixin(object):
    features = ["restart", ]

    def status(self):
        if self.resource.running:
            self.logger.debug("Running %r to determine if already running" % self.resource.running)
            try:
                platform.check_call(self.resource.running)
            except error.SystemError as e:
                self.logger.debug("Got exit code %d. Assuming not running." % (e.returncode, ))
                return "not-running"
            else:
                self.logger.debug("Got exit code 0. Assuming running.")
                return "running"

        if not self.resource.pidfile:
            self.logger.debug("Neither 'pidfile' nor 'running' option is set. Cannot determine service state.")
            return "unknown"

        self.logger.debug("Using pidfile %r to determine service state" % (self.resource.pidfile, ))

        if not platform.exists(self.resource.pidfile):
            self.logger.debug("The pidfile does not exist, service not running")
            return "not-running"

        try:
            pid = int(platform.get(self.resource.pidfile).strip())
        except:
            self.logger.debug("The pidfile could not be understood (should just contain a single int). Cannot determine service state.")
            return "unknown"

        # if platform.exists("/proc/%s" % pid):
        #     return "running"

        try:
            platform.check_call(["kill", "-0", str(pid)])
            self.logger.debug("Service is running.")
            return "running"
        except error.SystemError:
            self.logger.debug("Unable to kill(0) pid %d - service is not running." % pid)
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
        return getattr(self.resource, action)


class Start(_ServiceMixin, provider.Provider):

    policies = (resources.service.ServiceStartPolicy,)

    def apply(self):
        changed = self.ensure_enabled()

        if self.status() == "running":
            return changed

        self.do("start")

        return True


class Stop(_ServiceMixin, provider.Provider):

    policies = (resources.service.ServiceStopPolicy,)

    def apply(self):
        changed = self.ensure_disabled()

        if self.status() == "not-running":
            return changed

        self.do("stop")

        return True


class Restart(_ServiceMixin, provider.Provider):

    policies = (resources.service.ServiceRestartPolicy,)

    def apply(self):
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
