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

import six
from fuselage.tests.base import TestCaseWithRunner
from fuselage import platform


class TestFile(TestCaseWithRunner):

    def test_platform_exists(self):
        self.assertEqual(True, platform.exists("/etc/debconf.conf"))

    def test_platform_isfile(self):
        self.assertEqual(True, platform.isfile("/etc/debconf.conf"))

    def test_platform_isfile_FALSE(self):
        self.assertEqual(False, platform.isfile("/etc"))

    def test_platform_isdir(self):
        self.assertEqual(True, platform.isdir("/etc"))

    def test_platform_isdir_FALSE(self):
        self.assertEqual(False, platform.isdir("/etc/debconf.conf"))

    def test_platform_get(self):
        debconf = platform.get("/etc/debconf.conf")
        self.assertTrue(isinstance(debconf, six.string_types))
