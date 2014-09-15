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

import unittest
import mock

from libcloud.compute.ssh import BaseSSHClient

from fuselage.contrib.libcloud import FuselageDeployment


class MockClient(BaseSSHClient):

    def __init__(self, *args, **kwargs):
        self.stdout = ''
        self.stderr = ''
        self.exit_status = 0

    def put(self, path, contents, chmod=755, mode='w'):
        return contents

    def run(self, name):
        return self.stdout, self.stderr, self.exit_status

    def delete(self, name):
        return True


class TestLibcloud(unittest.TestCase):

    def test_simple_deployment(self):
        f = FuselageDeployment(bundle=None, resources=[])
        f.run(mock.Mock(), MockClient())
