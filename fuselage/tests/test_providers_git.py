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
from fuselage.resources import Package, Checkout
from fuselage import error


class TestGit(TestCaseWithRunner):

    def setUp(self):
        super(TestGit, self).setUp()
        self.p = self.bundle.add(Package(name="git", policy="install"))
        self.c = self.bundle.add(Checkout(
            scm='git',
            name="/dest",
            repository='git://github.com/isotoma/isotoma.recipe.django.git',
        ))

    def test_missing_git(self):
        self.p.policy = "uninstall"
        self.c.branch = "master"
        self.assertRaises(error.MissingDependency, self.apply)

    def test_clone(self):
        self.c.branch = "master"
        self.check_apply()

    def test_change_branch(self):
        self.c.branch = "master"
        self.check_apply()
        self.c.branch = "version3"
        self.check_apply()

    def test_checkout_tag(self):
        self.c.tag = "3.1.0"
        self.check_apply()

    def test_branch_to_tag(self):
        self.c.branch = "master"
        self.check_apply()
        self.c.branch = None
        self.c.tag = "3.1.0"
        self.check_apply()

    def test_change_repo(self):
        self.c.branch = "master"
        self.check_apply()

        self.c.repository = "http://github.com/isotoma/isotoma.recipe.django"
        self.check_apply()

    def test_checkout_revision(self):
        self.c.revision = "e24b4af3710201b011ba19752176645dcd9b0edc"
        self.check_apply()
