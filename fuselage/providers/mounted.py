# Copyright 2012-2014 Isotoma Limited
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

from fuselage import resources, provider, platform, error
from fuselage.changes import ShellCommand


class Mounted(provider.Provider):

    policies = (resources.checkout.CheckoutSyncPolicy,)

    @classmethod
    def isvalid(self, policy, resource):
        return resource.scm in ("dummy", "mounted", "mount")

    def apply(self):
        if not platform.exists(self.resource.name):
            return self.raise_or_log(error.PathComponentMissing(self.resource.name))

        for path in self.resource.changes:
            if platform.exists(path):
                self.logger.debug("Faking changes to %s" % (path, ))
                self.change(ShellCommand(["touch", "-ac", path]))
            else:
                self.logger.debug("Not faking changes to %s (file not present)" % (path, ))

        self.logger.debug("Faking that checkout changed")
        return True
