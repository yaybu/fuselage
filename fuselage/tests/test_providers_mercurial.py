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
from fuselage.resources import Package, Checkout, File
from fuselage import error


MIRRORS = """
deb http://uk.archive.ubuntu.com/ubuntu/ precise main restricted universe multiverse
deb http://uk.archive.ubuntu.com/ubuntu/ precise-updates main restricted universe multiverse
deb http://security.ubuntu.com/ubuntu precise-security main restricted universe multiverse
"""


class TestHg(TestCaseWithRunner):

    def setUp(self):
        super(TestHg, self).setUp()
        self.bundle.add(File(name="/etc/apt/sources.list", contents=MIRRORS))
        self.p = self.bundle.add(Package(name="mercurial", policy="install"))
        self.c = self.bundle.add(Checkout(
            scm='mercurial',
            name="/dest",
            repository='https://bitbucket.org/Jc2k/pkl/',
        ))

    def test_missing_hg(self):
        self.p.policy = "uninstall"
        self.c.branch = "issue_78"
        self.assertRaises(error.MissingDependency, self.apply)

    def test_clone(self):
        self.c.branch = "issue_78"
        self.check_apply()

    def test_change_branch(self):
        self.c.branch = "issue_78"
        self.check_apply()
        self.c.branch = "issue_84"
        self.check_apply()

    def test_checkout_tag(self):
        self.c.tag = "3.8"
        self.check_apply()

    def test_tag_to_tag(self):
        self.c.tag = "3.7"
        self.check_apply()
        self.c.tag = "3.8"
        self.check_apply()

    def test_branch_to_tag(self):
        self.c.branch = "issue_78"
        self.check_apply()
        self.c.branch = None
        self.c.tag = "3.8"
        self.check_apply()

    def test_checkout_revision(self):
        self.c.revision = "d9ac715eae35ce5befe9711ed360d7806bf46bb4"
        self.apply()
