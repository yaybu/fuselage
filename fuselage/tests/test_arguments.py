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

from fuselage import argument, resource, error


class TestArguments(unittest.TestCase):

    def test_octal(self):
        class R_test_octal(resource.Resource):
            a = argument.Octal()
        self.assertTrue(isinstance(R_test_octal.a, argument.Octal))
        r = R_test_octal(id="test")
        r.a = "666"
        self.assertEqual(r.a, 438)
        r.a = 0o666
        self.assertEqual(r.a, 438)

    def test_string(self):
        class R_test_string(resource.Resource):
            a = argument.String()
        self.assertTrue(isinstance(R_test_string.a, argument.String))
        r = R_test_string(id="test")
        r.a = "foo"
        self.assertEqual(r.a, "foo")
        r.a = u"foo"
        self.assertEqual(r.a, "foo")

    def test_integer(self):
        class R_test_integer(resource.Resource):
            a = argument.Integer()
        self.assertTrue(isinstance(R_test_integer.a, argument.Integer))
        r = R_test_integer(id="test")
        r.a = 10
        self.assertEqual(r.a, 10)
        r.a = "10"
        self.assertEqual(r.a, 10)
        r.a = 10.5
        self.assertEqual(r.a, 10)

        self.assertRaises(error.ParseError, setattr, r, "a", "one")

    def test_boolean(self):
        class R_test_bool(resource.Resource):
            a = argument.Boolean()
        self.assertTrue(isinstance(R_test_bool.a, argument.Boolean))
        r = R_test_bool(id="test")
        r.a = True
        self.assertEqual(r.a, True)
        r.a = False
        self.assertEqual(r.a, False)
        r.a = "ON"
        self.assertEqual(r.a, True)
        r.a = "yes"
        self.assertEqual(r.a, True)
        r.a = "1"
        self.assertEqual(r.a, True)
        #r.a = "off"
        #self.assertEqual(r.a, False)

    #def test_full_path(self):
    #    class R_test_full_path(resource.Resource):
    #        a = argument.FullPath()
    #    self.assertTrue(isinstance(R_test_full_path.a, argument.FullPath))
    #    self.assertRaises(error.ParseError, R_test_full_path, id="test", a="test")
