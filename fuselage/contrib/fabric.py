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

from __future__ import absolute_import, print_function
import ConfigParser
import inspect
import os
import StringIO
import subprocess

try:
    from fabric import tasks
    from fabric.operations import put, sudo
    from fabric.api import env, settings
    from fabric import utils
except SyntaxError:
    raise ImportError("Fabric cannot be imported due to syntax errors. Are you using a supported version of python?")

from fuselage import bundle, builder, error


class Loader(object):

    def __init__(self, dirname):
        self._dirname = dirname

    @property
    def dirname(self):
        return self._dirname() if callable(self._dirname) else self._dirname

    def exists(self, path):
        return os.path.exists(os.path.join(self.dirname, path))

    def template(self, path, ctx):
        from jinja2 import Environment, FileSystemLoader
        e = Environment(loader=FileSystemLoader(self.dirname), line_statement_prefix='%')
        return e.get_template(path).render(ctx) + "\n"

    def static(self, path):
        with open(os.path.join(self.dirname, path), "rb") as fp:
            return fp.read()

    def decrypt(self, path):
        data = self.static(path)
        environ = os.environ.copy()
        if "GPG_TTY" not in environ and os.path.exists("/proc/self/fd/0"):
            environ['GPG_TTY'] = os.readlink('/proc/self/fd/0')
        p = subprocess.Popen(["gpg", "--use-agent", "--batch", "-d"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, env=environ)
        stdout, stderr = p.communicate(data)
        if p.returncode != 0:
            error_message = "Unable to decrypt data '%s'." % path
            if "GPG_AGENT_INFO" not in environ:
                error_message += " GPG Agent not running so your GPG key may not be available."
            utils.error(error_message)
            raise RuntimeError(error_message)
        return stdout


class Environment(ConfigParser.ConfigParser, object):

    def __init__(self, environment, dirname=None):
        super(Environment, self).__init__()
        self.loader = Loader(dirname or os.path.join(os.path.dirname(env.real_fabfile), "environments"))
        self.read("default.cfg")
        self.read("default-secrets.cfg.gpg")
        self.read(environment + ".cfg")
        self.read(environment + "-secrets.cfg.gpg")

    def read(self, path, required=False):
        fn = self.loader.decrypt if path.endswith(".gpg") else self.loader.static
        if not self.loader.exists(path):
            if required:
                utils.error("Configuration file '%s' not found" % path)
                raise RuntimeError
            return
        self.readfp(StringIO.StringIO(fn(path)))

    def iter_sections_starting(self, starting):
        for section in self.sections():
            if section.startswith(starting):
                yield section[len(starting):], dict(self.items(section))


class FuselageMixin(object):

    arguments = []

    def __init__(self, *args, **kwargs):
        super(FuselageMixin, self).__init__(*args, **kwargs)
        self.arguments = list(self.arguments)
        for arg in inspect.getargspec(self.wrapped).args:
            if arg not in ("bundle", ):
                self.arguments.append(arg)

        self.kwargs = {}
        for k, v in kwargs.items():
            if k in self.arguments:
                self.kwargs[k] = v

    def get_bundle_stream(self, *args, **kwargs):
        try:
            bun = bundle.ResourceBundle()
            bun.extend(self.wrapped(bun, *args, **kwargs))
        except error.Error as e:
            utils.error(str(e), exception=e)
            return

        return bun

    def apply_bundle(self, buffer, *args, **kwargs):
        raise NotImplementedError(self.apply_bundle)

    def run(self, *args, **kwargs):
        unsupported = set(kwargs.keys()).difference(set(self.arguments))
        if unsupported:
            utils.error("The following parameters were not understood: %s" % ", ".join(unsupported))
            return

        k = {}
        k.update(self.kwargs)
        k.update(kwargs)

        return self.apply_bundle(self.get_bundle_stream(*args, **k), *args, **k)

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    @classmethod
    def as_decorator(cls):
        def _(*args, **kwargs):
            invoked = bool(not args or kwargs)
            if not invoked:
                func, args = args[0], ()
            task_class = kwargs.pop("task_class", cls)

            def wrapper(func):
                return task_class(func, *args, **kwargs)

            return wrapper if invoked else wrapper(func)
        return _


class DeploymentTask(FuselageMixin, tasks.WrappedCallableTask):

    arguments = ['simulate', 'loglevel']

    def apply_bundle(self, bundle, *args, **kwargs):
        uploaded = put(builder.build(bundle), '~/payload.pex', mode=755)
        if uploaded.failed:
            utils.error("Could not upload fuselange bundle to target. Aborting.")
            return

        command = [uploaded[0]]

        if kwargs.get("simulate", "false").lower() in ("true", "y", "yes", "on", "1"):
            command.append("--simulate")

        if "loglevel" in kwargs:
            if kwargs['loglevel'].lower() not in ("info", "debug", ):
                utils.error("Invalid loglevel")
                return
            command.extend(["-v"] * {"info": 0, "debug": 1}[kwargs['loglevel'].lower()])

        try:
            with settings(warn_only=True):
                result = sudo(" ".join(command))

                if not result.return_code in (0, 254):
                    utils.error("Could not apply fuselage blueprint. Aborting.")
                    return

        finally:
            sudo("rm %s" % uploaded[0])

blueprint = DeploymentTask.as_decorator()


class DockerBuildTask(FuselageMixin, tasks.WrappedCallableTask):

    arguments = ['from_image', 'tag', 'env', 'ports', 'volumes', 'cmd', 'maintainer']

    def apply_bundle(self, bundle, *args, **kwargs):
        from fuselage.docker import DockerBuilder
        d = DockerBuilder(bundle, **kwargs)
        try:
            for data in d.build():
                utils.puts(data, flush=True, end='')
        except RuntimeError as e:
            utils.error(str(e))
            return

docker_container = DockerBuildTask.as_decorator()


loader = Loader(lambda: os.path.join(os.path.dirname(env.real_fabfile), "deployment"))
template = loader.template
static = loader.static
decrypt = loader.decrypt
