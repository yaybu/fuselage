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
import six

try:
    from fabric import tasks
    from fabric.operations import put, sudo
    from fabric.api import settings
    from fabric import utils
except SyntaxError:
    raise ImportError("Fabric cannot be imported due to syntax errors. Are you using a supported version of python?")

from fuselage import bundle, builder, error


class FuselageMixin(object):

    arguments = []

    def get_bundle_stream(self, *args, **kwargs):
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

        buffer.seek(0)

        return buffer

    def apply_bundle(self, buffer, *args, **kwargs):
        raise NotImplementedError(self.apply_bundle)

    def run(self, *args, **kwargs):
        unsupported = set(kwargs.keys()).difference(set(self.arguments))
        if unsupported:
            utils.error("The following parameters were not understood: %s" % ", ".join(unsupported))
            return

        return self.apply_bundle(self.get_bundle_stream(*args, **kwargs), *args, **kwargs)

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

    arguments = ['simulate']

    def apply_bundle(self, bundle, *args, **kwargs):
        uploaded = put(bundle, '~/payload.pex', mode=755)
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

blueprint = DeploymentTask.as_decorator()


class DockerBuildTask(FuselageMixin, tasks.WrappedCallableTask):

    arguments = ['from_image', 'tag']

    def apply_bundle(self, bundle, from_image='ubuntu', tag=None, *args, **kwargs):
        import docker
        import tarfile
        import json

        tar_buffer = six.BytesIO()
        tar = tarfile.open(mode='w:gz', fileobj=tar_buffer)

        def add(name, buf, mode=0o644):
            ti = tarfile.TarInfo(name=name)
            ti.size = len(buf.buf)
            ti.mode = mode
            tar.addfile(tarinfo=ti, fileobj=buf)

        add("payload.pex", bundle, mode=0o755)

        add("Dockerfile", six.BytesIO("\n".join([
            "FROM %s" % from_image,
            "ADD payload.pex /payload.pex",
            'RUN apt-get update && apt-get install python -y',
            'RUN /payload.pex',
            'RUN rm /payload.pex',
        ])))

        tar.close()
        tar_buffer.seek(0)

        c = docker.Client(
            base_url='unix://var/run/docker.sock',
            version='1.12',
            timeout=10,
        )

        build_output = c.build(
            fileobj=tar_buffer,
            custom_context=True,
            stream=True,
            rm=True,
            tag=tag,
        )

        status = None
        for data in build_output:
            data = json.loads(data)
            if 'status' in data:
                # {u'status': u'Downloading', u'progressDetail': {u'current': 3239, u'start': 141059980, u'total': 133813}, u'id': u'2124c4204a05', u'progress': u'[=>] 32.32 kB/1.338 MB 29s'}
                if status != data['status']:
                    status = data['status']
                    utils.puts(status, flush=True, end='')
                else:
                    utils.puts('.', show_prefix=False, flush=True, end='')
            else:
                utils.puts('', show_prefix=False, flush=True)
                status = None

                if 'stream' in data:
                    utils.puts(data['stream'])
                elif 'errorDetail' in data:
                    utils.error(data['error'])
                    return

docker_container = DockerBuildTask.as_decorator()
