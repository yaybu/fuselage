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
import json
import tarfile

import six

try:
    import docker
except ImportError:
    docker = None

from fuselage.builder import build


class DockerBuilder(object):

    def __init__(self, bundle, from_image='ubuntu', tag=None, env=None, volumes=None, ports=None, cmd=None, maintainer=None):
        self.bundle = bundle
        self.from_image = from_image
        self.tag = tag
        self.env = env or {}
        self.volumes = volumes or []
        self.ports = ports or []
        self.cmd = cmd
        self.maintainer = maintainer

    def get_dockerfile(self):
        df = [
            '# This Dockerfile was automatically generated by fuselage',
        ]

        if self.maintainer:
            df.append("MAINTAINER %s" % self.maintainer)

        df.append("FROM %s" % self.from_image or 'ubuntu')
        df.append("")

        for k, v in self.env.items():
            df.append("ENV %s %s" % (k, v))

        if self.volumes:
            df.append("VOLUME %s" % json.dumps(self.volumes))

        if self.ports:
            df.append("EXPOSE %s" % " ".join(str(p) for p in self.ports))

        if self.env or self.volumes or self.ports:
            df.append("")

        df.extend([
            'RUN if [[ -f /usr/bin/apt-get ]]; then apt-get update && apt-get install python -y; fi',
            'RUN if [[ -f /usr/bin/yum ]]; then yum install python -y; fi',
            '',
            "ADD payload.pex /payload.pex",
            'RUN /payload.pex',
            'RUN rm /payload.pex',
        ])

        if self.cmd:
            df.append("")
            df.append("CMD %s" % json.dumps(self.cmd))

        return "\n".join(df)

    def build(self):
        tar_buffer = six.BytesIO()
        tar = tarfile.open(mode='w:gz', fileobj=tar_buffer)

        def add(name, buf, mode=0o644):
            ti = tarfile.TarInfo(name=name)
            ti.size = len(buf.buf)
            ti.mode = mode
            tar.addfile(tarinfo=ti, fileobj=buf)

        add("payload.pex", build(self.bundle), mode=0o755)
        add("Dockerfile", six.BytesIO(self.get_dockerfile()))

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
            tag=self.tag,
        )

        status = None
        for data in build_output:
            data = json.loads(data)
            if 'status' in data:
                # {u'status': u'Downloading', u'progressDetail': {u'current': 3239, u'start': 141059980, u'total': 133813}, u'id': u'2124c4204a05', u'progress': u'[=>] 32.32 kB/1.338 MB 29s'}
                if status != data['status']:
                    if status:
                        yield '\n'
                    status = data['status']
                    yield status
                else:
                    yield '.'
            else:
                if status:
                    yield '\n'
                    status = None

                if 'stream' in data:
                    yield data['stream']
                elif 'errorDetail' in data:
                    raise RuntimeError(data['errorDetail'])
