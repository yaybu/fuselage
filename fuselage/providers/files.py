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
from fuselage.changes import ShellCommand, EnsureFile


class File(provider.Provider):

    """ Provides file creation using templates or static files. """

    policies = (resources.file.FileApplyPolicy,)

    def check_path(self, directory):
        if platform.isdir(directory):
            self.logger.debug("Prereq: %r is a directory" % directory)
            return
        frags = directory.split("/")
        path = "/"
        for i in frags:
            path = os.path.join(path, i)
            if not platform.exists(path):
                self.raise_or_log(error.PathComponentMissing("Directory '%s' is missing" % path))
            elif not platform.isdir(path):
                raise error.PathComponentNotDirectory("Path '%s' is not a directory" % path)

    def apply(self):
        name = self.resource.name

        self.check_path(os.path.dirname(name))

        if self.resource.source:
            if self.resource.source.startswith("bundle://"):
                import pkgutil
                loader = pkgutil.get_loader("fuselage")
                contents = loader.get_data("assets/" + self.resource.source[9:])
            else:
                with open(self.resource.source, "rb") as fp:
                    contents = fp.read()
        else:
            contents = self.resource.contents

        fc = EnsureFile(
            name,
            contents,
            self.resource.owner,
            self.resource.group,
            self.resource.mode,
            sensitive=self.resource.sensitive,
        )
        self.change(fc)

        return fc.changed


class RemoveFile(provider.Provider):
    policies = (resources.file.FileRemovePolicy,)

    def get_delete_command(self):
        if platform.platform == "win32":
            return ["cmd.exe", "/C", "DEL", "/Q", "/F"]
        return ["rm"]

    def apply(self):
        name = self.resource.name
        if platform.exists(name):
            if not platform.isfile(name):
                raise error.InvalidProvider("%s exists and is not a file" % name)
            self.change(ShellCommand(self.get_delete_command() + [self.resource.name]))
            changed = True
        else:
            self.logger.debug("File %s missing already so not removed" % name)
            changed = False
        return changed


class WatchFile(provider.Provider):
    policies = (resources.file.FileWatchedPolicy, )

    def apply(self):
        """ Watched files don't have any policy applied to them """
        return self.resource.hash() != self.resource._original_hash
