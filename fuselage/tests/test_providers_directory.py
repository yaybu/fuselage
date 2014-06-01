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

import stat

from fuselage.tests.base import TestCaseWithRunner
from fuselage.resources import Directory
from fuselage import platform


class TestDirectory(TestCaseWithRunner):

    def test_create_directory(self):
        self.bundle.add(Directory(
            name="/etc/somedir",
            owner="root",
            group="root",
        ))
        self.check_apply()
        self.failUnless(platform.isdir("/etc/somedir"))

    def test_create_directory_and_parents(self):
        self.bundle.add(Directory(
            name="/etc/foo/bar/baz",
            parents=True,
        ))
        self.check_apply()
        self.failUnless(platform.isdir("/etc/foo/bar/baz"))

    def test_remove_directory(self):
        platform.makedirs("/etc/somedir")
        self.bundle.add(Directory(
            name="/etc/somedir",
            policy="remove",
        ))
        self.check_apply()
        self.failIfExists("/etc/somedir")

    def test_remove_directory_recursive(self):
        platform.makedirs("/etc/somedir")
        platform.put("/etc/somedir/child", "")
        self.bundle.add(Directory(
            name="/etc/somedir",
            policy="remove-recursive",
        ))
        self.check_apply()
        self.failIfExists("/etc/somedir")

    def test_unicode(self):
        self.bundle.add(Directory(
            name="/etc/☃",
            owner="root",
            group="root",
        ))
        self.check_apply()
        self.failUnlessExists("/etc/☃")

    def test_attributes(self):
        self.bundle.add(Directory(
            name="/etc/somedir",
            owner="nobody",
            group="nogroup",
            mode=0o777,
        ))
        self.check_apply()
        self.failUnlessExists("/etc/somedir")
        st = platform.stat("/etc/somedir")
        self.assertEqual(platform.getpwuid(st.st_uid)[0], 'nobody')
        self.assertEqual(platform.getgrgid(st.st_gid)[0], 'nogroup')
        mode = stat.S_IMODE(st.st_mode)
        self.assertEqual(mode, 0o777)
