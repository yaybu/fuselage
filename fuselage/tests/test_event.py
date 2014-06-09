# Copyright 2013-2014 Isotoma Limited
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
from fuselage.resources import File, Directory
from fuselage import platform, error


class TestEvent(TestCaseWithRunner):

    def test_nochange(self):
        self.bundle.add(Directory(name="/etc/wibble"))
        self.check_apply()

        # (Bundle still contains the directory at this point)
        self.bundle.add(File(name="/etc/test_nochange", watches=["/etc/wibble"]))
        self.assertRaises(error.NothingChanged, self.apply)

        self.failIfExists("/etc/test_nochange")

    def test_recover(self):
        self.bundle.add(Directory(name="/etc/somedir"))
        self.bundle.add(Directory(name="/frob/somedir"))
        self.bundle.add(File(name="/frob/somedir/foo", watches=["/etc/somedir"]))
        self.assertRaises(error.PathComponentMissing, self.apply)

        platform.check_call(["mkdir", "/frob"])
        self.check_apply()
        self.failUnlessExists("/frob/somedir/foo")
