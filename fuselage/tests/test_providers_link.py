# vim: set fileencoding=utf-8 :
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

from fuselage.tests.base import TestCaseWithRunner
from fuselage.resources import Link
from fuselage import platform, error


class TestLink(TestCaseWithRunner):

    def symlink(self, a, b):
        platform.check_call(["ln", "-s", a, b])

    def test_create_link(self):
        self.bundle.add(Link(
            name="/etc/create_link",
            to="/etc",
        ))
        self.check_apply()
        self.failUnless(platform.islink("/etc/create_link"))

    def test_unicode(self):
        self.bundle.add(Link(
            name="/etc/☃",
            to="/etc",
        ))
        self.check_apply()
        self.failUnlessExists("/etc/☃")

    def test_remove_link(self):
        self.symlink("/", "/etc/remove_link")
        self.bundle.add(Link(
            name="/etc/remove_link",
            policy="remove",
        ))
        self.check_apply()
        self.failIfExists("/etc/remove_link")

    def test_already_exists(self):
        self.symlink("/", "/etc/already_exists")
        self.bundle.add(Link(
            name="/etc/already_exists",
            to="/",
        ))
        self.assertRaises(error.NothingChanged, self.apply)
        self.failUnlessEqual(platform.readlink("/etc/already_exists"), "/")

    def test_already_exists_notalink(self):
        platform.put("/etc_already_exists_notalink", "")
        platform.put("/foo", "")
        self.bundle.add(Link(
            name="/etc/already_exists_notalink",
            to="/foo",
        ))
        self.check_apply()
        self.failUnlessEqual(platform.readlink("/etc/already_exists_notalink"), "/foo")

    def test_already_exists_points_elsewhere(self):
        platform.put("/baz", "")
        platform.put("/foo", "")
        self.symlink("/baz", "/bar_elsewhere")
        self.bundle.add(Link(
            name="/etc/bar_elsewhere",
            to="/foo",
        ))
        self.check_apply()
        self.failUnlessEqual(platform.readlink("/etc/bar_elsewhere"), "/foo")

    def test_dangling(self):
        self.bundle.add(Link(
            name="/etc/dangling",
            to="/etc/not/there",
        ))
        self.assertRaises(error.DanglingSymlink, self.apply)
