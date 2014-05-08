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
import json

from fuselage import error, resources, provider
from fuselage.changes import ShellCommand, EnsureFile


class File(provider.Provider):

    """ Provides file creation using templates or static files. """

    policies = (resources.file.FileApplyPolicy,)

    def check_path(self, ctx, directory, simulate):
        if os.path.isdir(directory):
            return
        frags = directory.split("/")
        path = "/"
        for i in frags:
            path = os.path.join(path, i)
            if not os.path.exists(path):  # FIXME
                if not simulate:
                    raise error.PathComponentMissing("Directory '%s' is missing" % path)
            elif not os.path.isdir(path):
                raise error.PathComponentNotDirectory("Path '%s' is not a directory" % path)

    def render_json(self, context):
        args = self.resource.args

        contents = json.dumps(args, sort_keys=True, indent=4)
        sensitive = self.resource.args.contains_secrets()
        return contents, sensitive

    def render_static(self, context):
        source = self.resource.source
        if not source:
            source = self.resource.static.as_string(default='')
            if not source:
                raise error.NoMatching("You must specify a 'source'")

        fp = context.get_file(source)
        contents = fp.read()
        sensitive = "secret" in fp.labels
        return contents, sensitive

    def render_empty(self, context):
        return None, False

    def render_guess(self, context):
        try:
            return self.render_static(context)
        except error.NoMatching:
            pass

        return self.render_empty(context)

    def render(self, context):
        renderer = self.resource.renderer.as_string(default='guess')
        func_name = 'render_%s' % renderer
        if not hasattr(self, func_name):
            raise error.ValueError("Invalid renderer '%s'" % renderer)
        return getattr(self, func_name)(context)

    def test(self, context):
        with context.root.ui.throbber("Checking '%s can be rendered" % self.resource):
            self.render(context)

    def apply(self, context, output):
        name = self.resource.name

        self.check_path(context, os.path.dirname(name), context.simulate)

        contents, sensitive = self.render(context)

        fc = EnsureFile(
            name,
            contents,
            self.resource.owner,
            self.resource.group,
            self.resource.mode,
            sensitive)
        context.change(fc)

        return fc.changed


class RemoveFile(provider.Provider):
    policies = (resources.file.FileRemovePolicy,)

    def apply(self, context, output):
        name = self.resource.name
        if os.path.exists(name):
            if not os.path.isfile(name):
                raise error.InvalidProvider(
                    "%s exists and is not a file" % name)
            context.change(ShellCommand(["rm", self.resource.name]))
            changed = True
        else:
            output.debug(
                "File %s missing already so not removed" % name)
            changed = False
        return changed


class WatchFile(provider.Provider):
    policies = (resources.file.FileWatchedPolicy, )

    def apply(self, context, output):
        """ Watched files don't have any policy applied to them """
        return self.resource.hash(context) != self.resource._original_hash
