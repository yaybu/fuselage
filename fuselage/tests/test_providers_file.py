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

import os
import stat
import tempfile

from fuselage.tests.base import TestCaseWithRunner, TestCaseWithRealRunner
from fuselage.resources import File
from fuselage import error, platform


class TestFileIntegration(TestCaseWithRealRunner):

    def test_file_apply(self):
        with tempfile.NamedTemporaryFile(delete=True) as fp:
            fp.close()
            self.bundle.add(File(
                name=fp.name,
                contents="hello",
            ))
            self.check_apply()
            self.assertTrue(os.path.exists(fp.name))
            self.assertEquals(open(fp.name, "r").read(), "hello")

    def test_file_remove(self):
        with tempfile.NamedTemporaryFile(delete=False) as fp:
            fp.write(b"HELLO")

        self.bundle.add(File(
            name=fp.name,
            policy="remove",
        ))
        self.check_apply()
        self.assertFalse(os.path.exists(fp.name))


class TestFile(TestCaseWithRunner):

    def test_not_directory(self):
        self.bundle.add(File(name="/etc/missing"))
        self.bundle.add(File(name="/etc/missing/filename"))
        self.assertRaises(error.PathComponentNotDirectory, self.apply)

    def test_create_missing_component(self):
        self.bundle.add(File(name="/etc/create_missing_component/filename"))
        self.assertRaises(error.PathComponentMissing, self.apply)

    def test_create_missing_component_simulate(self):
        """
        Right now we treat missing directories as a warning in simulate mode, as other outside processes might have created them.
        Later on we might not generate warnings for resources we can see will be created
        """
        self.bundle.add(File(name="/etc/missing/filename"))
        self.apply(simulate=True)

    def test_create_file(self):
        self.bundle.add(File(name="/etc/somefile"))
        self.check_apply()
        self.failUnlessExists("/etc/somefile")

    def test_create_file_unicode(self):
        self.bundle.add(File(name="/etc/test_create_file_☃"))
        self.check_apply()
        self.failUnlessExists("/etc/test_create_file_☃")

    def test_attributes(self):
        self.bundle.add(File(
            name="/etc/somefile",
            owner="nobody",
            group="nogroup",
            mode=0o666,
        ))
        self.check_apply()
        self.failUnlessExists("/etc/somefile")

        st = platform.stat("/etc/somefile")
        self.assertEqual(platform.getpwuid(st.st_uid)[0], 'nobody')
        self.assertEqual(platform.getgrgid(st.st_gid)[0], 'nogroup')
        mode = stat.S_IMODE(st.st_mode)
        self.assertEqual(mode, 0o666)

    def test_contents(self):
        self.bundle.add(File(
            name="/etc/somefile",
            contents="test contents",
        ))
        self.check_apply()
        self.assertEqual(platform.get("/etc/somefile"), "test contents")

    def test_modify_file(self):
        platform.put("/etc/test_modify_file", "foo\nbar\baz")

        self.bundle.add(File(
            name="/etc/test_modify_file",
            contents="test contents",
        ))
        self.check_apply()
        self.assertEqual(platform.get("/etc/test_modify_file"), "test contents")

    def test_empty_file(self):
        platform.put("/etc/test_empty_file", "foo\nbar\baz")

        self.bundle.add(File(
            name="/etc/test_empty_file",
            contents="",
        ))
        self.check_apply()
        self.assertEqual(platform.get("/etc/test_empty_file"), "")


class TestFileRemove(TestCaseWithRunner):

    def test_remove_file(self):
        platform.put("/etc/test_remove_file", "foo\nbar\baz")
        self.bundle.add(File(
            name="/etc/test_remove_file",
            policy="remove",
        ))
        self.check_apply()
        self.failIfExists("/etc/test_remove_file")

    def test_remove_missing(self):
        self.failIfExists("/etc/test_remove_missing")
        self.bundle.add(File(
            name="/etc/test_remove_missing",
            policy="remove",
        ))
        self.assertRaises(error.NothingChanged, self.apply)

    def test_remove_notafile(self):
        platform.makedirs("/etc/test_remove_notafile")
        self.bundle.add(File(
            name="/etc/test_remove_notafile",
            policy="remove",
        ))
        self.assertRaises(error.InvalidProvider, self.apply)
