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
from fuselage.changes import ShellCommand


class Mount(provider.Provider):

    policies = (resources.mount.MountPolicy,)

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
                self.raise_or_log(error.PatchComponentMissing(path))
            if not platform.isdir(path):
                raise error.PathComponentNotDirectory(path)

    def get_all_active_mounts(self):
        path = platform.get("/proc/mounts")
        d = {}
        for line in path.split("\n"):
            if not line.strip():
                continue

            split = line.split()
            d[split[1]] = {
                "fs_type": split[0],
                "mountpoint": split[1],
                "device": split[2],
                "options": split[3],
                "dump": split[4],
                "fsck": split[5],
            }
        return d

    def get_mount(self, path):
        return self.get_all_active_mounts()[path]

    def apply(self):
        name = self.resource.name

        self.check_path(name)

        try:
            self.get_mount(name)
            return

        except KeyError:
            command = ["mount"]

            fs_type = self.resource.fs_type
            if fs_type:
                if fs_type == "bind":
                    command.append("--bind")
                else:
                    command.extend(("-t", fs_type))
            command.append(self.resource.device)
            command.append(self.resource.name)

            options = self.resource.options
            if options:
                command.extend(("-o", options))

            self.change(ShellCommand(
                command=command,
            ))
            return True
