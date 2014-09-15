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

from fuselage import error, resources, provider, platform
from fuselage.changes import EnsureFile


class Patch(provider.Provider):

    """ Provides file creation using templates or static files. """

    policies = (resources.patch.PatchApplyPolicy,)

    def check_path(self, directory):
        if platform.isdir(directory):
            return
        frags = directory.split("/")
        path = "/"
        for i in frags:
            path = os.path.join(path, i)
            if not platform.exists(path):
                self.raise_or_log(error.PathComponentMissing(path))
            elif not platform.isdir(path):
                raise error.PathComponentNotDirectory(path)

    def apply_patch(self):
        patch = self.resource.patch
        try:
            stdout, stderr = platform.check_call(
                command=[
                    'patch', '-t', '--dry-run', '-N', '--silent',
                    '-r', '-', '-o', '-', self.resource.source, '-'
                ],
                stdin=patch,
            )
        except error.SystemError as e:
            self.logger.error("Patch does not apply cleanly")
            self.logger.error(
                "Patch file used was %s" % self.resource.patch)
            self.logger.error(
                "File to patch was %s" % self.resource.source)

            self.logger.error("")
            self.logger.error("Reported error was:")
            map(self.logger.error, e.stderr.split("\n"))

            raise error.CommandError("Unable to apply patch")

        return stdout

    def apply(self):
        name = self.resource.name

        self.check_path(os.path.dirname(name))

        contents = self.apply_patch()

        fc = EnsureFile(name, contents, self.resource.owner,
                        self.resource.group, self.resource.mode, sensitive=self.resource.sensitive)
        self.change(fc)

        return fc.changed
