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
from fuselage.resources import Patch
from fuselage import error, platform


EMPTY_FILE_DIFF = """
--- empty_file  2013-09-03 10:03:18.684478066 +0100
+++ hello_world 2013-09-14 23:23:15.367744089 +0100
@@ -0,0 +1 @@
+hello {{ everybody }}
"""


class TestPatch(TestCaseWithRunner):

    def test_path_missing_component(self):
        self.bundle.add(Patch(
            name="/etc/missing/filename",
            source="/etc/missing/filename",
            patch=EMPTY_FILE_DIFF,
        ))
        self.assertRaises(error.PathComponentMissing, self.apply)

    def test_simple_patch(self):
        platform.put("/etc/simple_patch", "")
        self.bundle.add(Patch(
            name="/etc/simple_patch.out",
            source="/etc/simple_patch",
            patch=EMPTY_FILE_DIFF,
        ))
        self.check_apply()
