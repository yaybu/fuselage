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
from fuselage.resources import Line
from fuselage import platform, error


class TestLine(TestCaseWithRunner):

    def test_target_doesnt_exist(self):
        self.bundle.add(Line(
            name="/target_doesnt_exist",
            match="^FOO",
            line="FOO 2",
            linesep="\n",
        ))
        self.assertRaises(error.PathComponentMissing, self.apply)

    def test_replace_existing_line_start(self):
        platform.put("/replace_existing_line_start", "FOO 1\nBAR 2\nBAZ 3")
        self.bundle.add(Line(
            name="/replace_existing_line_start",
            match="^FOO",
            line="FOO 2",
            linesep="\n",
        ))
        self.check_apply()
        self.assertEqual(platform.get("/replace_existing_line_start"), "FOO 2\nBAR 2\nBAZ 3")

    def test_replace_existing_line_middle(self):
        platform.put("/replace_existing_line_middle", "FOO 1\nBAR 2\nBAZ 3")
        self.bundle.add(Line(
            name="/replace_existing_line_middle",
            match="^BAR",
            line="BAR 1",
            linesep="\n",
        ))
        self.check_apply()
        self.assertEqual(platform.get("/replace_existing_line_middle"), "FOO 1\nBAR 1\nBAZ 3")

    def test_replace_existing_line_end(self):
        platform.put("/replace_existing_line_end", "FOO 1\nBAR 2\nBAZ 3")
        self.bundle.add(Line(
            name="/replace_existing_line_end",
            match="^BAZ",
            line="BAZ 2",
            linesep="\n",
        ))
        self.check_apply()
        self.assertEqual(platform.get("/replace_existing_line_end"), "FOO 1\nBAR 2\nBAZ 2")

    def test_replace_existing_line_append(self):
        platform.put("/replace_existing_line_append", "FOO 1\nBAR 2\nBAZ 3")
        self.bundle.add(Line(
            name="/replace_existing_line_append",
            match="^QUX",
            line="QUX 2",
            linesep="\n",
        ))
        self.check_apply()
        self.assertEqual(platform.get("/replace_existing_line_append"), "FOO 1\nBAR 2\nBAZ 3\nQUX 2")

    def test_remove_line(self):
        platform.put("/replace_existing_line_append", "FOO 1\nBAR 2\nBAZ 3")
        self.bundle.add(Line(
            name="/replace_existing_line_append",
            policy="remove",
            match="^BAR",
            linesep="\n",
        ))
        self.check_apply()
        self.assertEqual(platform.get("/replace_existing_line_append"), "FOO 1\nBAZ 3")

    def test_multiple_lines(self):
        platform.put("/multiple_lines", "FOO 1\nBAR 2\nBAZ 3")
        self.bundle.add(Line(
            name="/multiple_lines",
            match="^BAR",
            line="BAR 3",
            linesep="\n",
        ))
        self.bundle.add(Line(
            name="/multiple_lines",
            match="^BAZ",
            line="BAZ 4",
            linesep="\n",
        ))
        self.bundle.add(Line(
            name="/multiple_lines",
            match="^FOO",
            line="FOO 2",
            linesep="\n",
        ))
        self.check_apply()
        self.assertEqual(platform.get("/multiple_lines"), "FOO 2\nBAR 3\nBAZ 4")
