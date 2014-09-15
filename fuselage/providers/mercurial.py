# Copyright 2013-2014 Isotoma Limited
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
try:
    from urllib.parse import urlparse, urlunparse, quote
except ImportError:
    from urlparse import urlparse, urlunparse
    from urllib import quote


from fuselage import error, resources, provider, platform
from fuselage.changes import ShellCommand, EnsureFile, EnsureDirectory


hgrc = """
[paths]
default = %(repository)s
[extensions]
should = %(path)s/.hg/should.py
"""

mercurial_ext = """
from mercurial import util, hg, node

def should_pull(ui, repo, **opts):
    default_path = repo.ui.configlist('paths', 'default')[0]

    if not hasattr(hg, "peer"):
        source, revs, checkout = hg.parseurl(ui.expandpath(default_path), [])
        peer = hg.repository(ui, source)
    else:
        peer = hg.peer(ui, {}, default_path)

    remote_branches = peer.branchmap()
    local_branches = repo.branchmap()

    if opts['branch'] not in remote_branches:
        raise util.Abort('NO_SUCH_BRANCH: "%s" is not in the repository' % opts['branch'])

    if opts['branch'] not in local_branches:
        raise util.Abort('PULL: "%s" in not local, but is available in remote' % opts['branch'])

    if not opts['tag']:
        if remote_branches[opts['branch']] != local_branches[opts['branch']]:
            raise util.Abort('PULL: "%s" is out of date' % opts['branch'])

        ui.write("OK: Up to date")

    else:
        if not opts['tag'] in repo.tags().keys():
           raise util.Abort('PULL: "%s" is not in local' % opts['tag'])

        ui.write("OK: Tag is already available locally")


def should_update(ui, repo, **opts):
    if opts['tag']:
        target = opts['tag']
        revmap = repo.tags()
        if not target in revmap:
            raise util.Abort("FAIL: Tag '%s' not found locally" % target)
        targetrev = [revmap[target]]
    else:
        target = opts['branch']
        revmap = repo.branchmap()
        if not target in revmap:
            raise util.Abort("FAIL: Branch '%s' not found locally" % target)
        targetrev = revmap[target]

    localrev = [node.short(p.node()) for p in repo[None].parents()]
    targetrev = [node.short(p) for p in targetrev]

    if localrev != targetrev:
        raise util.Abort("UPDATE: Checkout is at '%s', target '%s' is at revision '%s'" % (localrev, target, targetrev))

    ui.write("OK: Checkout is up to date")


cmdtable = {
    'should-pull': (should_pull, [('b', 'branch', 'default', 'Branch to track'), ('t', 'tag', '', 'Tag to track')], '[options]'),
    'should-update': (should_update, [('b', 'branch', 'default', 'Branch to track'), ('t', 'tag', '', 'Tag to track')], '[options]'),
    }
"""


def _inject_credentials(url, username=None, password=None):
    if username and password:
        p = urlparse(url)
        netloc = '%s:%s@%s' % (
            quote(username, ''),
            quote(password, ''),
            p.hostname,
        )
        if p.port:
            netloc += ":" + str(p.port)
        url = urlunparse(
            (p.scheme, netloc, p.path, p.params, p.query, p.fragment))
    return url


class Mercurial(provider.Provider):

    policies = (resources.checkout.CheckoutSyncPolicy,)

    @classmethod
    def isvalid(self, policy, resource):
        return resource.scm and resource.scm.lower() == "mercurial"

    def get_hg_command(self, action, *args):
        command = [
            "hg",
            action,
        ]

        command.extend(list(args))
        return command

    def info(self, action, *args):
        return platform.check_call(
            command=self.get_hg_command(action, *args),
            user=self.resource.user,
            cwd=self.resource.name,
        )

    def should_update(self, *args):
        try:
            self.info("should-update", *args)
        except error.SystemError as e:
            self.logger.debug("'should-update' test has failed")
            self.logger.debug(e.stdout)
            return True
        return False

    def should_pull(self, *args):
        try:
            self.info("should-pull", *args)
        except error.SystemError as e:
            self.logger.debug("'should-pull' test has failed")
            self.logger.debug(e.stdout)
            return True
        return False

    def action(self, action, *args):
        self.change(ShellCommand(
            self.get_hg_command(action, *args),
            user=self.resource.user,
            cwd=self.resource.name,
        ))

    def apply(self):
        if not platform.exists("/usr/bin/hg"):
            self.raise_or_log(error.MissingDependency(
                "'/usr/bin/hg' is not available; update your configuration to install mercurial?"
            ))
            return

        created = False
        changed = False

        self.change(EnsureDirectory(self.resource.name,
                       self.resource.user, self.resource.group, 0o755))

        if not platform.exists(os.path.join(self.resource.name, ".hg")):
            try:
                self.action("init")
            except error.SystemError:
                raise error.CheckoutError("Cannot initialise local repository.")
            created = True

        url = _inject_credentials(self.resource.repository,
                                  self.resource.scm_username, self.resource.scm_password)

        try:
            self.change(EnsureFile(
                os.path.join(self.resource.name, ".hg", "hgrc"),
                hgrc % {"repository": url, "path":
                        self.resource.name},
                self.resource.user,
                self.resource.group,
                0o600,
                sensitive=bool(self.resource.scm_password),
            ))
            # changed = changed or f.changed
        except error.SystemError:
            raise error.CheckoutError("Could not set the remote repository.")

        try:
            self.change(EnsureFile(
                os.path.join(
                    self.resource.name, ".hg", "should.py"),
                mercurial_ext,
                self.resource.user,
                self.resource.group,
                0o600,
            ))
            # changed = changed or f.changed
        except error.SystemError:
            raise error.CheckoutError(
                "Could not setup mercurial idempotence extension")

        should_args = []
        if self.resource.branch:
            should_args.extend(["-b", self.resource.branch])
        if self.resource.tag:
            should_args.extend(["-t", self.resource.tag])

        if created or self.should_pull(*should_args):
            try:
                self.action("pull", "--force")
                changed = True
            except error.SystemError:
                raise error.CheckoutError(
                    "Could not fetch changes from remote repository."
                )

        if created or self.should_update(*should_args):
            if self.resource.tag:
                args = [self.resource.tag]
            elif self.resource.branch:
                args = [self.resource.branch]
            else:
                args = []

            try:
                self.action("update", *args)
                changed = True
            except error.SystemError:
                raise error.CheckoutError(
                    "Could not update working copy."
                )

        return created or changed
