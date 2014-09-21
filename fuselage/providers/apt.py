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


def is_installed(resource):
    # work out if the package is already installed
    command = ["dpkg-query", "-W", "-f='${Status}'", resource.name]

    try:
        stdout, stderr = platform.check_call(command)
    except error.SystemError as exc:
        if exc.returncode == 1:
            return False
        # if the return code is anything but zero or one, we have a problem
        raise error.PackageError(
            "%s search failed with return code %s" % (resource, exc.returncode))

    # if the return code is 0, dpkg is aware of the package
    if "install ok installed" in stdout:
        return True

    return False


class AptInstall(provider.Provider):

    policies = (resources.package.PackageInstallPolicy,)

    @classmethod
    def isvalid(self, policy, resource):
        if resource.backend and resource.backend != "apt":
            return False
        return True

    def apply(self):
        if is_installed(self.resource):
            self.logger.debug("Package already installed; nothing to do.")
            return False

        env = {
            "DEBIAN_FRONTEND": "noninteractive",
        }

        # the search returned 1, package is not installed, continue and install
        # it
        command = ["apt-get", "install", "-q", "-y", "--force-yes", self.resource.name]

        try:
            self.change(ShellCommand(command, env=env))
        except error.SystemError as exc:
            if exc.returncode == 100:
                try:
                    self.change(
                        ShellCommand(["apt-get", "update", "-q", "-y"], env=env))
                    self.change(ShellCommand(command, env=env))
                except error.SystemError as exc:
                    raise error.PackageError(
                        "%s with what looked like a recoverable error, but it wasn't (return code %d)" %
                        (self.resource, exc.returncode))
            else:
                raise error.PackageError(
                    "%s failed with return code %d" %
                    (self.resource, exc.returncode))

        return True


class AptUninstall(provider.Provider):

    policies = (resources.package.PackageUninstallPolicy,)

    @classmethod
    def isvalid(self, policy, resource):
        if resource.backend and resource.backend != "apt":
            return False
        return True

    def apply(self):
        if not is_installed(self.resource):
            self.logger.debug("Package '%s' is already uninstalled, not removing." % self.resource.name)
            return False

        env = {
            "DEBIAN_FRONTEND": "noninteractive",
        }

        command = ["apt-get", "remove", "-q", "-y"]
        if self.resource.purge:
            command.append("--purge")
        command.append(self.resource.name)

        try:
            self.change(ShellCommand(command, env=env))
        except error.SystemError as exc:
            raise error.PackageError(
                "%s failed to uninstall with return code %d" % (self.resource, exc.returncode))

        return True
