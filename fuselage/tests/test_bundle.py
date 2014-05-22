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

import six
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
            watches=["File[/etc/apache2/sites-enabled/www-example-com]"],
        ))

    def test_add__bind_fails(self):
        self.assertRaises(error.BindingError, self.bundle.add, resources.Execute(
            name='restart-apache',
            command='apache2ctl graceful',
            watches=["File[/etc/apache2/sites-enabled/www-example-com]"],
        ))

    def test_add__bind_to_self(self):
        self.assertRaises(error.BindingError, self.bundle.add, resources.Execute(
            name='restart-apache',
            command='apache2ctl graceful',
            watches=["Execute[restart-apache]"],
        ))

    def test_create(self):
        # FIXME: dict is a pep8 workaround
        r = self.bundle.create("File", **dict(
            name="/tmp/example",
        ))
        self.assertEqual(r.name, "/tmp/example")
        self.assertEqual(len(self.bundle), 1)

    def test_load(self):
        self.bundle.load(six.StringIO("""
        {"version": 1, "resources": [{"File": {"name": "/tmp"}}]}
        """))
        self.assertEqual(self.bundle["File[/tmp]"].name, "/tmp")

    def test_loads(self):
        self.bundle.loads("""
        {"version": 1, "resources": [{"File": {"name": "/tmp"}}]}
        """)
        self.assertEqual(self.bundle["File[/tmp]"].name, "/tmp")

    def test_load_bundle__root_not_dict(self):
        self.assertRaises(error.ParseError, self.bundle._load_bundle, [])

    def test_load_bundle__no_version(self):
        self.assertRaises(error.ParseError, self.bundle._load_bundle, {
            "resources": [],
        })

    def test_load_bundle__version_too_new(self):
        self.assertRaises(error.ParseError, self.bundle._load_bundle, {
            "version": 9001,
            "resources": [],
        })

    def test_load_bundle__no_resources_key(self):
        self.assertRaises(error.ParseError, self.bundle._load_bundle, {
            "version": 1,
            "resourcees": [],
        })

    def test_load_bundle__resources_not_list(self):
        self.assertRaises(error.ParseError, self.bundle._load_bundle, {
            "version": 1,
            "resources": "hello",
        })

    def test_load_bundle__resources_res_not_dict(self):
        self.assertRaises(error.ParseError, self.bundle._load_bundle, {
            "version": 1,
            "resources": ["hello"],
        })

    def test_load_bundle__resources_too_few_keys(self):
        self.assertRaises(error.ParseError, self.bundle._load_bundle, {
            "version": 1,
            "resources": [{}],
        })

    def test_load_bundle__resources_too_many_keys(self):
        self.assertRaises(error.ParseError, self.bundle._load_bundle, {
            "version": 1,
            "resources": [
                {"Directory": {"name": "/tmp/baz"}, "File": {"name": "/tmp/foo"}},
            ],
        })

    def test_load_bundle__invalid_type(self):
        self.assertRaises(error.ParseError, self.bundle._load_bundle, {
            "version": 1,
            "resources": [
                {"Director": {"name": "/tmp/baz"}},
            ],
        })
