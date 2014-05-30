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
import unittest
import logging
import mock
import collections
import subprocess
from fakechroot import FakeChroot

from fuselage import bundle, runner, error


stat_result = collections.namedtuple("stat_result",
                                     ("st_mode", "st_ino", "st_dev", "st_nlink", "st_uid", "st_gid",
                                      "st_size", "st_atime", "st_mtime", "st_ctime"))

logger = logging.getLogger()


class TestCaseWithBundle(unittest.TestCase):

    def setUp(self):
        self.bundle = bundle.ResourceBundle()


class TestCaseWithRunner(TestCaseWithBundle):

    location = os.path.join(os.path.dirname(__file__), "..", "..")

    def setUp(self):
        logging.getLogger().setLevel(logging.DEBUG)

        self.logger = logging.getLogger(__name__)

        self.chroot = FakeChroot.create_in_tempdir(self.location)
        self.chroot.build()
        logger.debug("Created fakechroot @ %s" % self.chroot.chroot_path)

        self.patches = []

        def patch(odn):
            p = mock.patch(odn) #  , spec=True)
            self.patches.append(p)
            return p.start()

        patch("fuselage.platform.isfile").side_effect = \
            lambda path: os.path.isfile(self.chroot._enpathinate(path))
        patch("fuselage.platform.islink").side_effect = \
            lambda path: os.path.islink(self.chroot._enpathinate(path))
        patch("fuselage.platform.lexists").side_effect = \
            lambda path: os.path.lexists(self.chroot._enpathinate(path))
        patch("fuselage.platform.get").side_effect = \
            lambda path: self.chroot.open(path).read()
        patch("fuselage.platform.put").side_effect = \
            lambda path, contents, chmod=None: self.chroot.open(path, 'w').write(contents)
        patch("fuselage.platform.makedirs").side_effect = \
            lambda path: os.makedirs(self.chroot._enpathinate(path))
        patch("fuselage.platform.unlink").side_effect = \
            lambda path: os.unlink(self.chroot._enpathinate(path))

        patch("fuselage.platform.exists").side_effect = self.chroot.exists
        patch("fuselage.platform.isdir").side_effect = self.chroot.isdir
        patch("fuselage.platform.readlink").side_effect = self.chroot.readlink

        def check_call(command):
            p = subprocess.Popen(command, cwd=self.chroot.chroot_path, env=self.chroot.get_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            return p.returncode, stdout, stderr

        def stat(path):
            returncode, stdout, stderr = check_call(["stat", "-L", "-t", path])
            if returncode != 0:
                raise OSError
            data = stdout.split(" ")
            return stat_result(
                int(data[3], 16), # st_mode
                int(data[8]), # st_ino
                int(data[7], 16), # st_dev
                int(data[9]), # st_nlink
                int(data[4]), # st_uid
                int(data[5]), # st_gid
                int(data[1]), # st_size
                int(data[11]), # st_atime
                int(data[12]), # st_mtime
                int(data[13]), # st_ctime
            )
        patch("fuselage.platform.stat").side_effect = stat

        def lstat(path):
            returncode, stdout, stderr = check_call(["stat", "-t", path])
            if returncode != 0:
                raise OSError
            data = stdout.split(" ")
            return stat_result(
                int(data[3], 16), # st_mode
                int(data[8]), # st_ino
                int(data[7], 16), # st_dev
                int(data[9]), # st_nlink
                int(data[4]), # st_uid
                int(data[5]), # st_gid
                int(data[1]), # st_size
                int(data[11]), # st_atime
                int(data[12]), # st_mtime
                int(data[13]), # st_ctime
            )
        patch("fuselage.platform.lstat").side_effect = lstat

        p = mock.patch.dict("fuselage.platform.ENVIRON_OVERRIDE", self.chroot.get_env())
        p.start()
        self.patches.append(p)

        logger.debug("Patched platform layer with fakechroot monkeypatches")

        self.bundle = bundle.ResourceBundle()

    def tearDown(self):
        [p.stop() for p in self.patches]
        logger.debug("Monkey patches reverted")
        self.chroot.destroy()
        logger.debug("Fakechroot destroyed")

    def failUnlessExists(self, path):
        if not self.chroot.exists(path):
            self.fail("Path '%s' does not exist" % path)

    def failIfExists(self, path):
        if self.chroot.exists(path):
            self.fail("Path '%s' exists" % path)

    def apply(self, simulate=False):
        r = runner.Runner(self.bundle, simulate=simulate)
        return r.run()

    def check_apply(self):
        logger.debug("Simulating bundle apply")
        self.apply(simulate=True)

        logger.debug("Applying bundle")
        try:
            self.apply(simulate=False)
        except error.NothingChanged:
            self.fail("Their were no pending changes after simulate")

        logger.debug("Applying bundle again to check for idempotency")
        try:
            self.apply(simulate=False)
        except error.NothingChanged:
            return
        else:
            self.fail("After 2nd apply() their were still pending changes")
