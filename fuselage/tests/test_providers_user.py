# Copyright 2013 Isotoma Limited
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

from fuselage.tests.base import TestCaseWithRunner
from fuselage.resources import User, Group
from fuselage import error, platform


class TestUser(TestCaseWithRunner):

    def test_simple_user(self):
        self.bundle.add(User(name="test"))
        self.check_apply()
        platform.getpwnam("test")

    def test_disabled_login(self):
        self.bundle.add(User(name="test", disabled_login=True))
        self.check_apply()
        platform.getpwnam("test")

    def test_user_with_home(self):
        self.bundle.add(User(name="test", home="/home/foo"))
        self.check_apply()
        self.failUnlessExists("/home/foo")

    def test_user_with_impossible_home(self):
        self.bundle.add(User(name="test", home="/home/does/not/exist"))
        self.assertRaises(error.UserAddError, self.apply)

    def test_user_with_uid(self):
        self.bundle.add(User(name="test", uid=1111))
        self.check_apply()
        self.assertEqual(platform.getpwnam("test").pw_uid, 1111)

    def test_user_with_gid(self):
        self.bundle.add(Group(name="testgroup", gid=1122))
        self.bundle.add(User(name="test", gid=1122))
        self.check_apply()
        self.assertEqual(platform.getpwnam("test").pw_gid, 1122)

    def test_user_with_fullname(self):
        self.bundle.add(User(name="test", fullname="testy mctest"))
        self.check_apply()
        self.assertEqual(platform.getpwnam("test").pw_gecos, "testy mctest")

    def test_user_with_password(self):
        self.bundle.add(User(name="test", password="password"))
        self.check_apply()
        self.assertEqual(platform.getspnam("test").sp_pwd, "password")

    def test_user_with_group(self):
        self.bundle.add(User(name="test", group="nogroup"))
        self.check_apply()
        self.assertEqual(platform.getpwnam("test").pw_gid, platform.getgrnam("nogroup").gr_gid)

    def test_user_with_groups(self):
        self.bundle.add(User(name="test", groups=["nogroup"]))
        self.check_apply()
        self.assertTrue("test" in platform.getgrnam("nogroup").gr_mem)

    def test_user_with_groups_replace(self):
        self.bundle.add(User(name="test", groups=["nogroup"], append=False))
        self.check_apply()
        self.assertEqual(platform.getgrnam("nogroup").gr_mem, ["test"])


class TestUserRemove(TestCaseWithRunner):

    def test_remove_existing(self):
        self.assertTrue(platform.getpwnam("nobody"))
        self.bundle.add(User(name="nobody", policy="remove"))
        self.check_apply()
        self.assertRaises(KeyError, platform.getpwnam, "nobody")

    def test_remove_non_existing(self):
        self.assertRaises(KeyError, platform.getpwnam, "zzidontexistzz")
        self.bundle.add(User(name="zzidontexistzz", policy="remove"))
        self.assertRaises(error.NothingChanged, self.apply)
        self.assertRaises(KeyError, platform.getpwnam, "zzidontexistzz")
