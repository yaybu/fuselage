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
from fuselage.resources import Checkout, Directory, File
from fuselage import platform


class TestDummyCheckout(TestCaseWithRunner):

    def test_dummy_checkout(self):
        self.bundle.add(Directory(name="/dummy"))
        self.bundle.add(Checkout(
            name="/dummy",
            repository="",
            scm='dummy',
            changes=['/dummy/foo'],
        ))
        self.bundle.add(File(name="/dummy/change_detected", watches=['Checkout[/dummy]']))
        self.apply()
        self.failUnlessExists('/dummy/change_detected')

        # This step shouldn't be idempotent - its meant to be used with
        # vagrant's /vagrant - every 'vagrant provision' should re-run
        # migrations
        platform.unlink('/dummy/change_detected')
        self.apply()
        self.failUnlessExists('/dummy/change_detected')
