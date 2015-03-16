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
import logging
import re

from fuselage import error, resources, provider, platform
from fuselage.changes import ShellCommand, EnsureDirectory


log = logging.getLogger(__name__)


class Git(provider.Provider):

    policies = (resources.checkout.CheckoutSyncPolicy,)

    REMOTE_NAME = "origin"

    @classmethod
    def isvalid(self, policy, resource):
        return resource.scm and resource.scm.lower() == "git"

    def get_git_command(self, action, *args):
        command = [
            "git",
            # "--git-dir=%s" % os.path.join(self.resource.name, ".git"),
            # "--work-tree=%s" % self.resource.name,
            "--no-pager",
            action,
        ]

        command.extend(list(args))
        return command

    def info(self, action, *args):
        try:
            stdout, stderr = platform.check_call(
                self.get_git_command(action, *args),
                user=self.resource.user,
                cwd=self.resource.name,
            )
            returncode = 0
        except error.SystemError as e:
            returncode, stdout, stderr = e.returncode, e.stdout, e.stderr

        return returncode, stdout, stderr

    def action(self, action, *args):
        self.change(ShellCommand(
            self.get_git_command(action, *args),
            user=self.resource.user,
            cwd=self.resource.name,
        ))

    def action_clone(self):
        """Adds resource.repository as a remote, but unlike a
        typical clone, does not check it out

        """
        self.change(EnsureDirectory(self.resource.name,
                       self.resource.user, self.resource.group, 0o755))

        try:
            self.action("init", self.resource.name)
        except error.SystemError:
            raise error.CheckoutError("Cannot initialise local repository.")

        self.action_set_remote()

    def action_set_remote(self):
        try:
            self.action("remote", "add", self.REMOTE_NAME,
                        self.resource.repository)
        except error.SystemError:
            raise error.CheckoutError("Could not set the remote repository.")

    def action_update_remote(self):
        # Determine if the remote repository has changed
        remote_re = re.compile(self.REMOTE_NAME + r"\t(.*) \(.*\)\n")
        rv, stdout, stderr = self.info("remote", "-v")
        remote = remote_re.search(stdout)
        if remote:
            if not self.resource.repository == remote.group(1):
                log.info("The remote repository has changed.")
                try:
                    self.action("remote", "rm", self.REMOTE_NAME)
                except error.SystemError:
                    raise error.CheckoutError(
                        "Could not delete remote '%s'" % self.REMOTE_NAME)
                self.action_set_remote()
                return True
        else:
            raise error.CheckoutError("Cannot determine repository remote.")

        return False

    def checkout_needed(self):
        # Determine which SHA is currently checked out.
        if platform.exists(os.path.join(self.resource.name, ".git")):
            try:
                rv, stdout, stderr = self.info("rev-parse", "--verify", "HEAD")
            except error.SystemError:
                head_sha = '0' * 40
            else:
                head_sha = stdout[:40]
                log.info("Current HEAD sha: %s" % head_sha)
        else:
            head_sha = '0' * 40

        try:
            stdout, stderr = platform.check_call(
                command=["git", "ls-remote", self.resource.repository],
                user=self.resource.user,
                cwd="/tmp"
            )
        except error.SystemError:
            raise error.CheckoutError("Could not query the remote repository")

        r = re.compile('([0-9a-f]{40})\t(.*)\n')
        refs_to_shas = dict([(b, a) for (a, b) in r.findall(stdout)])

        # Revision takes precedent over branch

        revision = self.resource.revision
        tag = self.resource.tag
        branch = self.resource.branch

        if revision:
            newref = revision
            if newref != head_sha:
                return newref

        elif tag:
            as_tag = "refs/tags/%s" % tag
            if as_tag not in refs_to_shas.keys():
                raise error.CheckoutError("Cannot find a tag called '%s'" % tag)

            annotated_tag = as_tag + "^{}"
            if annotated_tag in refs_to_shas.keys():
                as_tag = annotated_tag
            newref = tag
            if head_sha != refs_to_shas.get(as_tag):
                return newref

        elif branch:
            as_branch = "refs/heads/%s" % branch
            if as_branch not in refs_to_shas.keys():
                raise error.CheckoutError(
                    "Cannot find a branch called '%s'" % branch)
            newref = "remotes/%s/%s" % (
                self.REMOTE_NAME,
                branch
            )
            if head_sha != refs_to_shas.get(as_branch):
                return newref
        else:
            raise error.CheckoutError(
                "You must specify either a revision, tag or branch")

    def action_checkout(self, newref):
        try:
            self.action("fetch", self.REMOTE_NAME)
        except error.SystemError:
            raise error.CheckoutError("Could not fetch '%s'" %
                                self.resource.repository)

        try:
            self.action("checkout", newref)
        except error.SystemError:
            raise error.CheckoutError("Could not check out '%s'" % newref)

    def apply(self):
        if not platform.exists("/usr/bin/git"):
            self.raise_or_log(error.MissingDependency(
                "'/usr/bin/git' is not available; update your configuration to install git?"
            ))
            return

        # If necessary, clone the repository
        if not platform.exists(os.path.join(self.resource.name, ".git")):
            self.action_clone()
            changed = True
        else:
            changed = self.action_update_remote()

        newref = self.checkout_needed()
        if newref:
            self.action_checkout(newref)

        return changed or newref
