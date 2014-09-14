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

from fuselage import error, resource


class TestResource(unittest.TestCase):

    def test_redefinition(self):
        # Two classes of resource can't have the same __resource_name__
        raised = False
        try:
            class Dummy(resource.Resource):
                __resource_name__ = "Dummy"

            class Dummy2(resource.Resource):
                __resource_name__ = "Dummy"
        except error.ParseError:
            raised = True
        self.assertEqual(raised, True)

    def test_must_have_name(self):
        # By default a Resource must have a name
        self.assertRaises(error.ParseError, resource.Resource)

    def test_only_valid_kwargs(self):
        self.assertRaises(error.ParseError, resource.Resource, id="/foo", frob=True)

    def test_repr(self):
        r = resource.Resource(id="foo")
        self.assertEqual(repr(r), "Resource[foo]")

    def test_id(self):
        r = resource.Resource(id="foo")
        self.assertEqual(r.typed_id, "Resource[foo]")
