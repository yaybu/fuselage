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
from fuselage.changes import EnsureDirectory, ShellCommand


def dirname(p):
    i = p.rfind('/') + 1
    head = p[:i]
    if head and head != '/' * len(head):
        head = head.rstrip('/')
    return head


class Directory(provider.Provider):

    policies = (resources.directory.DirectoryAppliedPolicy,)

    def check_path(self, directory):
        if platform.isdir(directory):
            return

        frags = directory.split("/")
        path = "/"
        for i in frags:
            path = os.path.join(path, i)
            if not platform.exists(path):
                if self.resource.parents:
                    return
                self.raise_or_log(error.PathComponentMissing(path))
            if not platform.isdir(path):
                raise error.PathComponentNotDirectory(path)

    def apply(self):
        name = self.resource.name

        # FIXME: This should use os.path.name - but then what about tests that
        # rely on posix behaviour?
        # Need to mark those as skipped on nt and implement tests that exercise
        # simple behaviour on posix and nt
        self.check_path(dirname(name))

        return self.change(EnsureDirectory(
            name,
            self.resource.owner,
            self.resource.group,
            self.resource.mode,
            self.resource.parents,
        ))


class RemoveDirectory(provider.Provider):

    policies = (resources.directory.DirectoryRemovedPolicy,)

    def apply(self):
        name = self.resource.name

        if platform.exists(name) and not platform.isdir(name):
            raise error.InvalidProviderError(
                "%r: %s exists and is not a directory" % (self, name))
        if platform.exists(name):
            self.change(ShellCommand(["/bin/rmdir", self.resource.name]))
            changed = True
        else:
            changed = False
        return changed


class RemoveDirectoryRecursive(provider.Provider):

    policies = (resources.directory.DirectoryRemovedRecursivePolicy,)

    def apply(self):
        name = self.resource.name

        if platform.exists(name) and not platform.isdir(name):
            raise error.InvalidProviderError(
                "%r: %s exists and is not a directory" % (self, name))
        if platform.exists(name):
            self.change(
                ShellCommand(["/bin/rm", "-rf", self.resource.name]))
            changed = True
        else:
            changed = False
        return changed
