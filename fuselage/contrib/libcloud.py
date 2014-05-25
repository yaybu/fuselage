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

import binascii
import os
import six

from libcloud.compute import deployment

from fuselage.bundle import ResourceBundle
from fuselage import builder


class FuselageDeployment(deployment.Deployment):

    def __init__(self, bundle=None, resources=None):
        self.bundle = bundle

        if not self.bundle:
            self.bundle = ResourceBundle()

        if resources:
            for resource in resources:
                self.bundle.add(resource)

    def run(self, node, client):
        random_string = binascii.hexlify(os.urandom(4)).decode('ascii')
        name = 'fuselage_%s' % (random_string)

        buffer = six.BytesIO()
        buffer.name = name

        bu = builder.Builder.write_to(buffer)
        bu.embed_fuselage_runtime()
        bu.embed_resource_bundle(self.bundle)
        bu.close()

        file_path = client.put(path=name, chmod=0o755, contents=bu.getvalue())
        self.stdout, self.stderr, self.exit_status = client.run(file_path)
        client.delete(name)
        return node
