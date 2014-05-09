# coding=utf-8
# Copyright 2011-2014 Isotoma Limited
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

from fuselage import argument
from fuselage import resource


class TestArguments(unittest.TestCase):

    def test_octal(self):
        class R_test_octal(resource.Resource):
            a = argument.Octal()
        r = R_test_octal(name="test")
        r.a = "666"
        self.assertEqual(r.a, 438)
        r.a = 666
        self.assertEqual(r.a, 438)

    def test_string(self):
        class R_test_string(resource.Resource):
            a = argument.String()
        r = R_test_string(name="test")
        r.a = "foo"
        self.assertEqual(r.a, "foo")
        r.a = u"foo"
        self.assertEqual(r.a, "foo")
        r.a = u"£40"
        self.assertEqual(r.a, u"£40")
        r.a = u"£40".encode("utf-8")
        self.assertEqual(r.a, u"£40")

    def test_integer(self):
        class R_test_integer(resource.Resource):
            a = argument.Integer()
        r = R_test_integer(name="test")
        r.a = 10
        self.assertEqual(r.a, 10)
        r.a = "10"
        self.assertEqual(r.a, 10)
        r.a = 10.5
        self.assertEqual(r.a, 10)
