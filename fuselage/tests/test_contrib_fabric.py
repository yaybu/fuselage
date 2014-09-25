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

import unittest
import mock
import zipfile

from fuselage import resources

try:
    from fuselage.contrib import fabric
except ImportError:
    fabric = None


class FabricError(Exception):
    pass


class TestFabric(unittest.TestCase):

    def setUp(self):
        self.cleanup = []
        if not fabric:
            return

        for api in ("put", "sudo", "settings", "utils"):
            p = mock.patch("fuselage.contrib.fabric.%s" % api)
            setattr(self, api, p.start())
            self.cleanup.append(p)

        p = mock.patch("fuselage.contrib.fabric.env")
        self.env = p.start()
        self.cleanup.append(p)

        self.error = self.utils.error
        self.error.side_effect = FabricError()
        self.sudo.return_value.return_code = 0
        self.put.return_value.failed = []
        self.put.return_value.__getitem__.return_value = '~/payload.pex'
        self.env.real_fabfile = '/fabfile.py'

    def cleanUp(self):
        [x.stop() for x in self.cleanup()]

    def test_success(self):
        if not fabric:
            return

        @fabric.blueprint
        def example(bundle, **kwargs):
            yield resources.File(name='/tmp/hello')
        example()
        self.assertEqual(self.sudo.called, True)

        z = zipfile.ZipFile(self.put.call_args[0][0])
        z.getinfo("__main__.py")
        z.getinfo("resources.json")
        z.getinfo("fuselage/runner.py")

    def test_parse_error(self):
        if not fabric:
            return

        @fabric.blueprint
        def example(bundle, **kwargs):
            yield resources.File(nam='/tmp/hello')
        self.assertRaises(FabricError, example)
        self.assertEqual(self.sudo.called, False)
