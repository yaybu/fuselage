# Copyright 2014 Isotoma Limited
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
    command = ['rpm', '-q', resource.name]
    try:
        stdout, stderr = platform.check_call(command)
    except error.SystemError as exc:
        if exc.returncode == 1:
            return False

        raise error.PackageError("%s search failed with return code %s" % (resource, exc.returncode))

    return True


class YumInstall(provider.Provider):

    policies = (resources.package.PackageInstallPolicy,)

    @classmethod
    def isvalid(self, policy, resource):
        if resource.backend == "yum":
            return True
        return False

    def apply(self):
        if is_installed(self.resource):
            return False

        command = ["yum", "install", "-y", self.resource.name]

        try:
            self.change(ShellCommand(command))
        except error.SystemError as exc:
            raise error.PackageError(
                "%s failed with return code %d" %
                (self.resource, exc.returncode))

        return True


class YumUninstall(provider.Provider):

    policies = (resources.package.PackageUninstallPolicy,)

    @classmethod
    def isvalid(self, policy, resource):
        if resource.backend == "yum":
            return True
        return False

    def apply(self):
        if not is_installed(self.resource):
            return False

        command = ["yum", "remove", "-y", self.resource.name]

        try:
            self.change(ShellCommand(command))
        except error.SystemError as exc:
            raise error.PackageError(
                "%s failed to uninstall with return code %d" % (self.resource, exc.returncode))

        return True
