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
from fuselage.changes import EnsureContents


class Line(provider.Provider):

    policies = (resources.line.LineApplyPolicy,)

    def apply(self):
        if not platform.exists(self.resource.name):
            self.raise_or_log(error.PatchComponentMissing("File '%s' is missing" % self.resource.name))

        fc = EnsureContents(
            self.resource.name,
            platform.get(self.resource.name),
        )
        self.change(fc)

        return fc.changed
