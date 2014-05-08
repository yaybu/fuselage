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

import unittest

from fuselage import resource


class TestCheckout(unittest.TestCase):

    def test_repr(self):
        r = resource.Resource(name="foo")
        self.assertEqual(repr(r), "Resource[foo]")

    def test_id(self):
        r = resource.Resource(name="foo")
        self.assertEqual(r.id, "Resource[foo]")
