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
from fuselage.resources import Execute


test_execute_on_path = """
#!/bin/sh
touch /etc/test_execute_on_path
""".strip()


class TestExecute(TestCaseWithRunner):

    def test_not_directory(self):
        self.bundle.add(File(name="/etc/missing"))
        self.bundle.add(File(name="/etc/missing/filename"))
        self.assertRaises(error.PatchComponentNotDirectory, self.apply)

    def test_execute_on_path(self):
        platform.put(
            "/usr/bin/test_execute_on_path.sh", test_execute_on_path)
        platform.check_call(
            ["chmod", "0755", "/usr/bin/test_execute_on_path.sh"])

        self.bundle.add(Execute(
            name="test_execute_on_path",
            command="test_execute_on_path.sh",
            creates="/etc/test_execute_on_path",
        ))
        self.check_apply()
        self.failUnlessExists("/etc/test_execute_on_path")

    def test_execute_touches(self):
        self.bundle.add(Execute(
            name="test_execute_touches",
            command="echo HELLO",
            touches="/etc/test_execute_touches",
        ))
        self.check_apply()
        self.failUnlessExists("/etc/test_execute_touches")

    def test_creates(self):
        self.bundle.add(Execute(
            name="test_creates",
            command="touch /etc/test_creates",
            creates="/etc/test_creates",
        ))
        self.check_apply()
        self.failUnlessExists("/etc/test_creates")

    def test_commands(self):
        self.bundle.add(Execute(
            name="test_commands",
            commands=[
                "touch /etc/test_commands_1",
                "touch /etc/test_commands_2"
            ],
            creates="/etc/test_commands_2",
        ))
        self.check_apply()
        self.failUnlessExists("/etc/test_commands_1")
        self.failUnlessExists("/etc/test_commands_2")

    def test_cwd(self):
        self.bundle.add(Execute(
            name="test_cwd",
            command="touch test_cwd",
            cwd="/etc",
            creates="/etc/test_cwd",
        ))
        self.check_apply()
        self.failUnlessExists("/etc/test_cwd")

    def test_environment(self):
        self.bundle.add(Execute(
            name="test_environment",
            command="sh -c 'touch $FOO'"",
            env={
                "FOO": "/etc/test_environment"
            },
            creates="/etc/test_environment",
        ))
        self.check_apply()
        self.failUnlessExists("/etc/test_environment")

    def test_returncode(self):
        self.bundle.add(Execute(
            name="test_returncode",
            command="/bin/false",
            returncode=1,
            touch="/etc/test_returncode",
        ))
        self.check_apply()
        self.failUnlessExists("/etc/test_returncode")
