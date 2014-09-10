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
from fuselage.resources import Execute
from fuselage import error, platform


class TestExecute(TestCaseWithRunner):

    def test_execute_on_path(self):
        # Annoying fakechroot limitation
        # subprocess.Popen doesnt respect the PATH because execvp is *before* we are fakechrooted
        # So 'touch' is actually invoked from outside the fakechroot, but given an environment inside the fakechroot
        self.bundle.add(Execute(
            name="test_execute_on_path",
            command="touch /etc/test_execute_on_path",
            creates="/etc/test_execute_on_path",
        ))
        self.check_apply()
        self.failUnlessExists("/etc/test_execute_on_path")

    def test_execute_touches(self):
        self.bundle.add(Execute(
            name="test_execute_touches",
            command="echo HELLO",
            touch="/etc/test_execute_touches",
        ))
        self.check_apply()
        self.failUnlessExists("/etc/test_execute_touches")

    def test_touch_present(self):
        platform.put("/touched-file", "")
        self.bundle.add(Execute(
            name="test_touch_present",
            command="touch /checkpoint",
            touch="/touched-file",
        ))
        self.assertRaises(error.NothingChanged, self.apply)

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
            command="sh -c 'touch $FOO'",
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

    def test_user(self):
        self.bundle.add(Execute(
            name="test_user",
            command="python -c \"import os; open('/foo','w').write(str(os.getuid())+'\\n'+str(os.geteuid()))\"",
            user="nobody",
            creates="/foo",
        ))
        self.check_apply()
        check_file = platform.get("/foo").split()
        self.failUnlessEqual(["65534"] * 2, check_file)

    def test_group(self):
        self.bundle.add(Execute(
            name="test_user",
            command="python -c \"import os; open('/foo','w').write(str(os.getgid())+'\\n'+str(os.getegid()))\"",
            group="nogroup",
            creates="/foo",
        ))
        self.check_apply()
        check_file = platform.get("/foo").split()
        self.failUnlessEqual(["65534"] * 2, check_file)

    def test_user_and_group(self):
        self.bundle.add(Execute(
            name="test_user",
            command="python -c \"import os; open('/foo','w').write('\\n'.join(str(x) for x in (os.getuid(),os.geteuid(),os.getgid(),os.getegid())))\"",
            user="nobody",
            group="nogroup",
            creates="/foo",
        ))
        self.check_apply()
        check_file = platform.get("/foo").split()
        self.failUnlessEqual(["65534"] * 4, check_file)

    def test_unless_true(self):
        self.bundle.add(Execute(
            name="test",
            command="touch /test_unless_true",
            unless="/bin/true",
        ))
        self.assertRaises(error.NothingChanged, self.apply)

    def test_unless_false(self):
        self.bundle.add(Execute(
            name="test",
            command="touch /test_unless_false",
            unless="/bin/false",
            creates="/test_unless_false",
        ))
        self.check_apply()
        self.failUnlessExists("/test_unless_false")

    def test_umask_022(self):
        self.bundle.add(Execute(
            name="touch",
            command="touch /test_umask_022",
            umask=0o022,
            creates="/test_umask_022",
        ))
        self.check_apply()
        self.failUnlessExists("/test_umask_022")

        mode = stat.S_IMODE(platform.stat("/test_umask_022").st_mode)
        self.failUnlessEqual(mode, 0o644)

    def test_umask_002(self):
        self.bundle.add(Execute(
            name="touch",
            command="touch /test_umask_002",
            umask=0o002,
            creates="/test_umask_002",
        ))
        self.check_apply()
        self.failUnlessExists("/test_umask_002")

        mode = stat.S_IMODE(platform.stat("/test_umask_002").st_mode)
        self.failUnlessEqual(mode, 0o664)

    def test_missing_binary_absolute(self):
        self.bundle.add(Execute(
            name="test_missing_binary",
            command="/this_binary_definitely_doesnt_exist",
        ))
        self.assertRaises(error.BinaryMissing, self.apply)

    def test_implicit_name(self):
        self.bundle.add(Execute(
            command="touch /foo",
            creates="/foo",
        ))
        self.check_apply()
        self.failUnlessExists("/foo")

    def test_implicit_name_for_commands(self):
        self.bundle.add(Execute(
            commands=["touch /foo"],
            creates="/foo",
        ))
        self.check_apply()
        self.failUnlessExists("/foo")

    def test_implicit_name_watch_positive(self):
        self.bundle.add(Execute(
            command="touch /foo",
            creates="/foo",
        ))
        self.bundle.add(Execute(
            command="touch /bar",
            watches=['touch-foo'],
        ))
        self.check_apply()
        self.failUnlessExists("/bar")

    def test_implicit_name_watch_negative(self):
        self.bundle.add(Execute(
            command="touch /foo",
            creates="/bin/false",
        ))
        self.bundle.add(Execute(
            command="touch /bar",
            watches=['touch-foo'],
        ))
        self.assertRaises(error.NothingChanged, self.check_apply)
        self.failIfExists("/bar")
