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

from fuselage import error, resource, policy, argument


class DummyResource(resource.Resource):

    arg1 = argument.String()
    arg2 = argument.String()
    arg3 = argument.String()


class TestPolicy(unittest.TestCase):

    def test_validate_true(self):
        r = DummyResource(id="hello", arg1="hello")
        p = policy.Policy(r)
        p.signature = [policy.Present("arg1")]
        p.validate()

    def test_validate_false(self):
        r = DummyResource(id="hello")
        p = policy.Policy(r)
        p.signature = [policy.Present("arg1")]
        self.assertRaises(error.NonConformingPolicy, p.validate)

    def test_get_provider_no_suitable(self):
        r = DummyResource(id="hello")
        p = policy.Policy(r)
        self.assertRaises(error.NoSuitableProviders, p.get_provider)


class TestPresent(unittest.TestCase):

    def test_is_not_present(self):
        r = DummyResource(id="hello")
        p = policy.Present("arg1")
        self.assertEqual(False, p.test(r))
        self.assertEqual(["'arg1' must be present (False)"], list(p.describe(r)))

    def test_is_present(self):
        r = DummyResource(id="hello", arg1="i am present")
        p = policy.Present("arg1")
        self.assertEqual(True, p.test(r))
        self.assertEqual(["'arg1' must be present (True)"], list(p.describe(r)))


class TestAbsent(unittest.TestCase):

    def test_is_not_present(self):
        r = DummyResource(id="hello")
        p = policy.Absent("arg1")
        self.assertEqual(True, p.test(r))
        self.assertEqual(["'arg1' must be absent (True)"], list(p.describe(r)))

    def test_is_present(self):
        r = DummyResource(id="hello", arg1="i am present")
        p = policy.Absent("arg1")
        self.assertEqual(False, p.test(r))
        self.assertEqual(["'arg1' must be absent (False)"], list(p.describe(r)))


class TestAND(unittest.TestCase):

    def setUpAnd(self, arg1=None, arg2=None):
        kwargs = {"id": "hello"}
        if arg1:
            kwargs['arg1'] = arg1
        if arg2:
            kwargs['arg2'] = arg2
        r = DummyResource(**kwargs)
        p = policy.AND(policy.Present("arg1"), policy.Present("arg2"))
        return p.test(r), list(p.describe(r))

    def test_true_and_true(self):
        t, d = self.setUpAnd("foo", "bar")
        self.assertEqual(True, t)

    def test_true_and_false(self):
        t, d = self.setUpAnd("foo", None)
        self.assertEqual(False, t)

    def test_false_and_true(self):
        t, d = self.setUpAnd(None, "foo")
        self.assertEqual(False, t)

    def test_false_and_false(self):
        t, d = self.setUpAnd(None, None)
        self.assertEqual(False, t)


class TestNAND(unittest.TestCase):

    def setUpAnd(self, arg1=None, arg2=None):
        kwargs = {"id": "hello"}
        if arg1:
            kwargs['arg1'] = arg1
        if arg2:
            kwargs['arg2'] = arg2
        r = DummyResource(**kwargs)
        p = policy.NAND(policy.Present("arg1"), policy.Present("arg2"))
        return p.test(r), list(p.describe(r))

    def test_true_and_true(self):
        t, d = self.setUpAnd("foo", "bar")
        self.assertEqual(False, t)

    def test_true_and_false(self):
        t, d = self.setUpAnd("foo", None)
        self.assertEqual(True, t)

    def test_false_and_true(self):
        t, d = self.setUpAnd(None, "foo")
        self.assertEqual(True, t)

    def test_false_and_false(self):
        t, d = self.setUpAnd(None, None)
        self.assertEqual(True, t)


class TestOR(unittest.TestCase):

    def setUpAnd(self, arg1=None, arg2=None):
        kwargs = {"id": "hello"}
        if arg1:
            kwargs['arg1'] = arg1
        if arg2:
            kwargs['arg2'] = arg2
        r = DummyResource(**kwargs)
        p = policy.OR(policy.Present("arg1"), policy.Present("arg2"))
        return p.test(r), list(p.describe(r))

    def test_true_and_true(self):
        t, d = self.setUpAnd("foo", "bar")
        self.assertEqual(True, t)

    def test_true_and_false(self):
        t, d = self.setUpAnd("foo", None)
        self.assertEqual(True, t)

    def test_false_and_true(self):
        t, d = self.setUpAnd(None, "foo")
        self.assertEqual(True, t)

    def test_false_and_false(self):
        t, d = self.setUpAnd(None, None)
        self.assertEqual(False, t)
