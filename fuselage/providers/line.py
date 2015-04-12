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

import re

from fuselage import error, resources, provider, platform
from fuselage.changes import EnsureContents
from fuselage.utils import force_str


class _LineMixin(object):

    def apply(self):
        if not platform.exists(self.resource.name):
            self.raise_or_log(error.PathComponentMissing("File '%s' is missing" % self.resource.name))
            return

        lines = force_str(platform.get(self.resource.name)).splitlines()
        contents = self.resource.linesep.join(line for line in self.filter_lines(lines))

        fc = EnsureContents(
            self.resource.name,
            contents,
            sensitive=self.resource.sensitive,
        )
        self.change(fc)

        return fc.changed


class LineApply(_LineMixin, provider.Provider):

    policies = (resources.line.LineApplyPolicy,)

    def filter_lines(self, lines):
        regexp = re.compile(self.resource.match)
        matched = False
        for line in lines:
            if not matched and regexp.search(line):
                yield self.resource.line
                matched = True
            else:
                yield line

        if not matched:
            yield self.resource.line


class LineRemove(_LineMixin, provider.Provider):

    policies = (resources.line.LineRemovePolicy,)

    def filter_lines(self, lines):
        regexp = re.compile(self.resource.match)
        for line in lines:
            if not regexp.search(line):
                yield line
