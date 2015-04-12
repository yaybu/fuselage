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
import sys
import unittest
import tempfile
import shutil

from fuselage import platform, error
from fuselage.tests.base import skipIf


class TestPlatform(unittest.TestCase):

    @skipIf(sys.platform.startswith("win"), "requires *nix")
    def test_check_call(self):
        stdout, stderr = platform.check_call(['echo', 'hello'])
        self.assertEqual(stdout.strip(), 'hello')

    @skipIf(sys.platform.startswith("win"), "requires *nix")
    def test_check_call_FAIL(self):
        self.assertRaises(error.SystemError, platform.check_call, ['false'])

    def test_exists_file(self):
        self.assertEqual(True, platform.exists(__file__))

    def test_exists_dir(self):
        self.assertEqual(True, platform.exists(os.getcwd()))

    def test_isfile_TRUE(self):
        self.assertEqual(True, platform.isfile(__file__))

    def test_isfile_FALSE(self):
        self.assertEqual(False, platform.isfile(os.getcwd()))

    def test_isdir_TRUE(self):
        self.assertEqual(True, platform.isdir(os.getcwd()))

    def test_isdir_FALSE(self):
        self.assertEqual(False, platform.isdir(__file__))

    @skipIf(sys.platform.startswith("win"), "requires *nix")
    def test_islink_TRUE(self):
        p = __file__ + "test_islink_TRUE"
        os.symlink(__file__, p)
        try:
            self.assertEqual(True, platform.islink(p))
        finally:
            os.unlink(p)

    @skipIf(sys.platform.startswith("win"), "requires *nix")
    def test_islink_FALSE(self):
        self.assertEqual(False, platform.islink(__file__))

    def test_stat(self):
        # FIXME: Make some assertions!!
        platform.stat(__file__)

    @skipIf(sys.platform.startswith("win"), "requires *nix")
    def test_lexists_TRUE(self):
        p = __file__ + "test_lexists_TRUE"
        os.symlink(__file__, p)
        try:
            self.assertEqual(True, platform.lexists(p))
        finally:
            os.unlink(p)

    @skipIf(sys.platform.startswith("win"), "requires *nix")
    def test_readlink(self):
        p = __file__ + "test_readlink"
        os.symlink(__file__, p)
        try:
            self.assertEqual(platform.readlink(p), __file__)
        finally:
            os.unlink(p)

    @skipIf(sys.platform.startswith("win"), "requires *nix")
    def test_lstat(self):
        p = __file__ + "test_lstat"
        os.symlink(__file__, p)
        try:
            platform.lstat(p)
        finally:
            os.unlink(p)

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

    def test_makedirs(self):
        d1 = tempfile.mkdtemp()
        d2 = os.path.join(d1, "test_makedirs")
        try:
            platform.makedirs(d2)
            self.assertTrue(platform.isdir(d2))
        finally:
            shutil.rmtree(d1)

    @skipIf(sys.platform.startswith("win"), "requires *nix")
    def test_getgrall(self):
        if platform.gr_supported():
            self.assertTrue(isinstance(platform.getgrall(), list))

    @skipIf(sys.platform.startswith("win"), "requires *nix")
    def test_getgrgid(self):
        if platform.gr_supported():
            platform.getgrgid(os.getgid())

    @skipIf(sys.platform.startswith("win"), "requires *nix")
    def test_getgrname(self):
        if platform.gr_supported():
            grp = platform.getgrgid(os.getgid())
            platform.getgrnam(grp.gr_name)

    @skipIf(sys.platform.startswith("win"), "requires *nix")
    def test_getpwall(self):
        if platform.pwd_supported():
            self.assertTrue(isinstance(platform.getpwall(), list))

    @skipIf(sys.platform.startswith("win"), "requires *nix")
    def test_getpwuid(self):
        if platform.pwd_supported():
            platform.getgrgid(os.getgid())

    @skipIf(sys.platform.startswith("win"), "requires *nix")
    def test_getpwnam(self):
        if platform.pwd_supported():
            u = platform.getpwuid(os.getuid())
            platform.getpwnam(u.pw_name)

    @skipIf(sys.platform.startswith("win"), "requires *nix")
    def test_getspall(self):
        if platform.spwd_supported():
            self.assertTrue(isinstance(platform.getspall(), list))

    @skipIf(sys.platform.startswith("win"), "requires *nix")
    def test_getspnam(self):
        if platform.spwd_supported():
            passwords = platform.getspall()
            if not passwords:
                return
            platform.getspnam(passwords[0].sp_nam)

    @skipIf(sys.platform.startswith("win"), "requires *nix")
    def test_getuid(self):
        self.assertEqual(platform.getuid(), os.getuid())
