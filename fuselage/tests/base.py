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
import mock
from fakechroot import FakeChroot

from fuselage import bundle, runner


class TestCaseWithBundle(unittest.TestCase):

    def setUp(self):
        self.bundle = bundle.ResourceBundle()


class TestCaseWithRunner(TestCaseWithBundle):

    location = os.path.join(os.path.dirname(__file__), "..", "..")

    def setUp(self):
        self.chroot = FakeChroot.create_in_tempdir(self.location)
        self.chroot.build()

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
        patch("fuselage.platform.lstat").side_effect = \
            lambda path: os.lstat(self.chroot._enpathinate(path))
        patch("fuselage.platform.get").side_effect = \
            lambda path: self.chroot.open(path).read()
        patch("fuselage.platform.put").side_effect = \
            lambda path, contents, chmod: self.chroot.open(path, 'w').write(contents)
        patch("fuselage.platform.makedirs").side_effect = \
            lambda path: os.makedirs(self.chroot._enpathinate(path))
        patch("fuselage.platform.unlink").side_effect = \
            lambda path: os.unlink(self.chroot._enpathinate(path))

        patch("fuselage.platform.exists").side_effect = self.chroot.exists
        patch("fuselage.platform.isdir").side_effect = self.chroot.isdir
        patch("fuselage.platform.stat").side_effect = self.chroot.stat
        patch("fuselage.platform.readlink").side_effect = self.chroot.readlink

        p = mock.patch.dict("fuselage.platform.ENVIRON_OVERRIDE", self.chroot.get_env())
        p.start()
        self.patches.append(p)

        self.bundle = bundle.ResourceBundle()

    def cleanUp(self):
        [p.stop() for p in self.patches]
        self.chroot.destroy()

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
        self.apply(simulate=True)

        try:
            self.apply(simulate=False)
        except error.NothingChanged:
            self.fail("Their were no pending changes after simulate")

        try:
            self.apply(simulate=False)
        except error.NothingChanged:
            return
        else:
            self.fail("After 2nd apply() their were still pending changes")
