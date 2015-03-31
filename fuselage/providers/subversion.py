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
from fuselage.changes import ShellCommand, EnsureDirectory


class Svn(provider.Provider):

    policies = (resources.checkout.CheckoutSyncPolicy,)

    @classmethod
    def isvalid(self, policy, resource):
        identities = [
            'svn',
            'subversion',
        ]

        return resource.scm.lower() in identities

    @property
    def url(self):
        repository = self.resource.repository
        if self.resource.tag:
            return repository + "/tags/" + self.resource.tag
        return repository + "/" + self.resource.branch

    def apply(self):
        if not platform.exists("/usr/bin/svn"):
            self.raise_or_log(error.MissingDependency(
                "'/usr/bin/svn' is not available; update your configuration to install subversion?"
            ))

        self.change(EnsureDirectory(self.resource.name, self.resource.user, self.resource.group, 0o755))

        if not platform.exists(os.path.join(self.resource.name, ".svn")):
            self.svn("co", self.url, self.resource.name)
            return True

        changed = False

        info = self.info(self.resource.name)
        repo_info = self.info(self.url)

        # If the 'Repository Root' is different between the checkout and the
        # repo, switch --relocated
        old_repo_root = info["Repository Root"]
        new_repo_root = repo_info["Repository Root"]
        if old_repo_root != new_repo_root:
            self.changelog.info("Switching repository root from '%s' to '%s'" % (old_repo_root, new_repo_root))
            self.svn("switch", "--relocate",
                     old_repo_root, new_repo_root, self.resource.name)
            changed = True

        # If we have changed branch, switch
        old_url = info["URL"]
        new_url = repo_info["URL"]
        if old_url != new_url:
            self.changelog.info("Switching branch from '%s' to '%s'" % (old_url, new_url))
            self.svn("switch", new_url, self.resource.name)
            changed = True

        # If we have changed revision, svn up
        # FIXME: Eventually we might want revision to be specified in the
        # resource?
        current_rev = info["Last Changed Rev"]
        target_rev = repo_info["Last Changed Rev"]
        if current_rev != target_rev:
            self.changelog.info("Switching revision from %s to %s" % (current_rev, target_rev))
            self.svn("up", "-r", target_rev, self.resource.name)
            changed = True

        return changed

    def action_export(self):
        if platform.exists(self.resource.name):
            return
        self.svn("export", self.url, self.resource.name)

    def get_svn_args(self, action, *args, **kwargs):
        command = ["svn"]

        if kwargs.get("quiet", False):
            command.append("--quiet")

        command.extend([action, "--non-interactive"])

        scm_username = self.resource.scm_username
        scm_password = self.resource.scm_password
        if scm_username:
            command.extend(["--username", self.resource.scm_username])
        if scm_password:
            command.extend(["--password", self.resource.scm_password])
        if scm_username or scm_password:
            command.append("--no-auth-cache")

        for arg in args:
            command.append(arg)

        return command

    def info(self, uri):
        command = self.get_svn_args("info", uri)
        stdout, stderr = platform.check_call(command)
        return dict(x.split(": ") for x in stdout.split("\n") if x)

    def svn(self, action, *args, **kwargs):
        command = self.get_svn_args(action, *args, **kwargs)
        sc = ShellCommand(command, user=self.resource.user)
        self.change(sc)
