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

import os
import mock
import six
import unittest

from fuselage import platform, error


class TestPlatform(unittest.TestCase):

    def test_check_call(self):
        stdout, stderr = platform.check_call(['echo', 'hello'])
        self.assertEqual(stdout.strip(), 'hello')

    def test_check_call_FAIL(self):
        self.assertRaises(error.SystemError, platform.check_call, ['false'])

    def test_exists_file(self):
        self.assertEqual(True, platform.exists(__file__))
    
    def test_exists_dir(self):
        self.assertEqual(True, platform.exists(os.getcwd()))

    def test_isfile_TRUE(self):
        self.assertEqual(False, platform.isdir(__file__))

    def test_isfile_FALSE(self):
        self.assertEqual(True, platform.isdir(os.getcwd()))

    def test_isdir_TRUE(self):
        self.assertEqual(True, platform.isdir(os.getcwd()))

    def test_isdir_FALSE(self):
        self.assertEqual(False, platform.isdir(__file__))

    def test_stat(self):
        # FIXME: Make some assertions!!
        platform.stat(__file__)

    def test_get(self):
        self.assertTrue("platform" in platform.get(__file__))

    def test_put(self):
        path = os.path.join(os.getcwd(), "tmp_test_put")
        platform.put(path, "HELLO")
        try:
            self.assertTrue("HELLO" in platform.get(path))
        finally:
            platform.unlink(path)

    def test_put_replace(self):
        path = os.path.join(os.getcwd(), "tmp_test_put_replace")
        platform.put(path, "HELLO")
        try:
            self.assertTrue("HELLO" in platform.get(path))
            platform.put(path, "")
            self.assertTrue("HELLO" not in platform.get(path))
        finally:
            platform.unlink(path)

    def test_getgrall(self):
        if platform.gr_supported():
            self.assertTrue(isinstance(platform.getgrall(), list))

    def test_getpwall(self):
        if platform.pwd_supported():
            self.assertTrue(isinstance(platform.getpwall(), list))

    def test_getspall(self):
        if platform.spwd_supported():
            self.assertTrue(isinstance(platform.getspall(), list))
