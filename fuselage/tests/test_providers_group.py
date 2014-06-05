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
from fuselage.resources import Group
from fuselage import error, platform


class TestGroup(TestCaseWithRunner):

    def test_existing_group(self):
        platform.getgrnam("users")
        self.bundle.add(Group(name="users"))
        self.assertRaises(error.NothingChanged, self.apply)

    def test_simple_group(self):
        self.bundle.add(Group(name="test"))
        self.check_apply()
        platform.getgrnam("test")

    def test_existing_gid(self):
        self.bundle.add(Group(name="test", gid=100))
        self.assertRaises(error.InvalidGroup, self.apply)

    def test_group_with_gid(self):
        self.bundle.add(Group(name="test", gid=1111))
        self.check_apply()
        self.assertEqual(platform.getgrnam("test").gr_gid, 1111)


class TestGroupRemove(TestCaseWithRunner):

    def test_remove_existing(self):
        self.assertTrue(platform.getgrnam("users"))
        self.bundle.add(Group(name="users", policy="remove"))
        self.check_apply()
        self.assertRaises(KeyError, platform.getgrnam, "users")

    def test_remove_non_existing(self):
        self.assertRaises(KeyError, platform.getgrnam, "zzidontexistzz")
        self.bundle.add(Group(name="zzidontexistzz", policy="remove"))
        self.assertRaises(error.NothingChanged, self.apply)
        self.assertRaises(KeyError, platform.getgrnam, "zzidontexistzz")
