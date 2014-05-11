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

from fuselage import bundle, error, resources


class TestBundle(unittest.TestCase):

    def setUp(self):
        self.bundle = bundle.ResourceBundle()

    def test_add__simple(self):
        self.bundle.add(resources.File(
            name='/tmp/example',
            owner='root',
        ))
        self.assertEqual(len(self.bundle), 1)
        self.assertEqual(self.bundle['File[/tmp/example]'].name, '/tmp/example')

    def test_add__simple_no_duplicates(self):
        self.bundle.add(resources.File(
            name='/tmp/no_dupes',
        ))
        self.assertRaises(error.ParseError, self.bundle.add, resources.File(
            name='/tmp/no_dupes',
            owner='tim',
        ))

    def test_add__bind(self):
        self.bundle.add(resources.File(
            name='/etc/apache2/sites-enabled/www-example-com',
        ))
        self.bundle.add(resources.Execute(
            name='restart-apache',
            command='apache2ctl graceful',
            policy={"execute": {"when": "apply", "on": "File[/etc/apache2/sites-enabled/www-example-com]"}},
        ))

    def test_add__bind_fails(self):
        self.assertRaises(error.BindingError, self.bundle.add, resources.Execute(
            name='restart-apache',
            command='apache2ctl graceful',
            policy={"execute": {"when": "apply", "on": "File[/etc/apache2/sites-enabled/www-example-com]"}},
        ))

    def test_add__bind_to_self(self):
        self.assertRaises(error.BindingError, self.bundle.add, resources.Execute(
            name='restart-apache',
            command='apache2ctl graceful',
            policy={"execute": {"when": "apply", "on": "Execute[restart-apache]"}},
        ))

    def test_create(self):
        # FIXME: dict is a pep8 workaround
        r = self.bundle.create("File", **dict(
            name="/tmp/example",
        ))
        self.assertEqual(r.name, "/tmp/example")
        self.assertEqual(len(self.bundle), 1)
