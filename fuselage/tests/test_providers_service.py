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
from fuselage.resources import Service
from fuselage import platform, error


simpleservice = """
#! /usr/bin/env python
import os, select, sys, time
if __name__ == "__main__":
    if os.fork() != 0:
        os._exit(0)

    os.setsid()

    if os.fork() != 0:
        os._exit(0)

    open("simple_daemon.pid", "w").write(str(os.getpid()))
    #os.chdir("/")
    os.umask(0)

    for fd in range(0, 1024):
        try:
            os.close(fd)
        except OSError:
            pass

    os.open("/dev/null", os.O_RDWR)

    os.dup2(0, 1)
    os.dup2(0, 2)

    while True:
        time.sleep(60)
        select.select([sys.stdin], [], [])
"""


class TestService(TestCaseWithRunner):

    def setUp(self):
        super(TestService, self).setUp()
        platform.put("/bin/simpleservice", simpleservice)
        platform.check_call(["chmod", "755", "/bin/simpleservice"])

    def test_start(self):
        self.bundle.add(Service(
            name="test",
            policy="start",
            start="python /bin/simpleservice",
            pidfile="/simple_daemon.pid",
        ))
        try:
            self.check_apply()
        finally:
            pid = int(platform.get("/simple_daemon.pid"))
            platform.check_call(["kill", str(pid)])

    def test_start_running(self):
        self.bundle.add(Service(
            name="test",
            policy="start",
            start="touch /test_start_running",
            running="/bin/sh -c 'true'",
        ))
        self.assertRaises(error.NothingChanged, self.apply)
        self.failIfExists("/test_start_running")

    def test_start_not_running(self):
        self.bundle.add(Service(
            name="test",
            policy="start",
            start="touch /test_start_not_running",
            running="test -e /test_start_not_running",
        ))
        self.check_apply()
        self.failUnlessExists("/test_start_not_running")

    def test_stop(self):
        platform.check_call(["python", "/bin/simpleservice"])

        self.bundle.add(Service(
            name="test",
            policy="stop",
            stop="sh -c 'kill $(cat /simple_daemon.pid)'",
            pidfile="/simple_daemon.pid",
        ))
        self.check_apply()

    def test_restart(self):
        self.bundle.add(Service(
            name="test",
            policy="restart",
            restart="touch /restarted",
        ))
        self.apply()
        self.failUnlessExists("/restarted")
