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

import stat

from fuselage import error, resources, provider, platform
from fuselage.changes import ShellCommand


class Link(provider.Provider):

    policies = (resources.link.LinkAppliedPolicy,)

    def _get_owner(self):
        """ Return the uid for the resource owner, or None if no owner is
        specified. """
        owner = self.resource.owner
        if owner:
            try:
                return platform.getpwnam(owner).pw_uid
            except KeyError:
                raise error.InvalidUser()

    def _get_group(self):
        """ Return the gid for the resource group, or None if no group is
        specified. """
        group = self.resource.group
        if group:
            try:
                return platform.getgrnam(group).gr_gid
            except KeyError:
                raise error.InvalidGroup()

    def _stat(self):
        """ Extract stat information for the resource. """
        st = platform.lstat(self.resource.name)
        uid = st.st_uid
        gid = st.st_gid
        mode = stat.S_IMODE(st.st_mode)
        return uid, gid, mode

    def apply(self):
        changed = False
        name = self.resource.name
        to = self.resource.to
        uid = None
        gid = None
        mode = None
        isalink = False

        if not platform.exists(to):
            self.raise_or_log(error.DanglingSymlink(
                "Destination of symlink %r does not exist" % to
            ))

        owner = self._get_owner()
        group = self._get_group()

        try:
            linkto = platform.readlink(name)
            isalink = True
        except OSError:
            isalink = False

        if not isalink or linkto != to:
            if platform.lexists(name):
                self.change(
                    ShellCommand(["/bin/rm", "-rf", self.resource.name]))

            self.change(
                ShellCommand(["/bin/ln", "-s", self.resource.to, self.resource.name]))
            changed = True

        try:
            linkto = platform.readlink(name)
            isalink = True
        except OSError:
            isalink = False

        if not isalink:
            if not self.simulate:
                raise error.OperationFailed("Did not create expected symbolic link")
            return changed

        uid, gid, mode = self._stat()

        if owner and owner != uid:
            self.change(
                ShellCommand(["/bin/chown", "-h", self.resource.owner, self.resource.name]))
            changed = True

        if group and group != gid:
            self.change(
                ShellCommand(["/bin/chgrp", "-h", self.resource.group, self.resource.name]))
            changed = True

        return changed


class RemoveLink(provider.Provider):

    policies = (resources.link.LinkRemovedPolicy,)

    def apply(self):
        name = self.resource.name

        if platform.lexists(name):
            if not platform.islink(name):
                raise error.InvalidProvider(
                    "%r: %s exists and is not a link" % (self, name))
            self.change(ShellCommand(["/bin/rm", self.resource.name]))
            return True
        return False
