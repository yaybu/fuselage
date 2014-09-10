import unittest

from fuselage.utils import simple_str


class TestSimpleStr(unittest.TestCase):

    def test_no_op(self):
        self.assertEqual(simple_str("no-op"), "no-op")

    def test_simple_change(self):
        self.assertEqual(simple_str("simple change"), "simple-change")
