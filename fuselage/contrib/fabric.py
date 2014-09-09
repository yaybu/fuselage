# Copyright 2014 Isotoma Limited
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

from __future__ import absolute_import
import six

try:
    from fabric import tasks
    from fabric.operations import put, sudo
    from fabric.api import settings
    from fabric import utils
except SyntaxError:
    raise ImportError("Fabric cannot be imported due to syntax errors. Are you using a supported version of python?")

from fuselage import bundle, builder, error


class DeploymentTask(tasks.WrappedCallableTask):

    def run(self, *args, **kwargs):
        unsupported = set(kwargs.keys()).difference(set(["simulate"]))
        if unsupported:
            utils.error("The following parameters were not understood: %s" % ", ".join(unsupported))
            return

        try:
            bun = bundle.ResourceBundle()
            bun.extend(self.wrapped(bun, *args, **kwargs))
        except error.Error as e:
            utils.error(str(e), exception=e)
            return

        buffer = six.BytesIO()
        buffer.name = self.name

        bu = builder.Builder.write_to(buffer)
        bu.embed_fuselage_runtime()
        bu.embed_resource_bundle(bun)
        bu.close()

        uploaded = put(buffer, '~/payload.pex', mode=755)
        if uploaded.failed:
            utils.error("Could not upload fuselange bundle to target. Aborting.")
            return

        command = [uploaded[0]]

        if kwargs.get("simulate", "false").lower() in ("true", "y", "yes", "on", "1"):
            command.append("--simulate")

        try:
            with settings(warn_only=True):
                result = sudo(" ".join(command))

                if not result.return_code in (0, 254):
                    utils.error("Could not apply fuselage blueprint. Aborting.")
                    return

        finally:
            sudo("rm %s" % uploaded[0])

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)


def blueprint(*args, **kwargs):
    """
    Decorator declaring the wrapped function to be a resource generator that should be deployed.

    May be invoked as a simple, argument-less decorator (i.e. ``@blueprint``) or
    with arguments customizing its behavior (e.g. ``@blueprint(alias='myalias')``).
    """
    invoked = bool(not args or kwargs)
    if not invoked:
        func, args = args[0], ()

    task_class = kwargs.pop("task_class", DeploymentTask)

    def wrapper(func):
        return task_class(func, *args, **kwargs)

    return wrapper if invoked else wrapper(func)
