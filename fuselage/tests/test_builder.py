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
import zipfile

from fuselage import builder, bundle, resources


class TestBuilder(unittest.TestCase):

    def test_build_no_resources(self):
        fp = six.BytesIO()
        b = builder.Builder.write_to(fp)
        b.embed_fuselage_runtime()
        b.close()

        z = zipfile.ZipFile(six.BytesIO(fp.getvalue()))
        self.assertEqual(z.getinfo("__main__.py").file_size, len(builder.MAIN_PY))

    def test_build_resources(self):
        rb = bundle.ResourceBundle()
        rb.add(resources.User(name="matt"))
        fp = six.BytesIO()
        b = builder.Builder.write_to(fp)
        b.embed_fuselage_runtime()
        b.embed_resource_bundle(rb)
        b.close()

        z = zipfile.ZipFile(six.BytesIO(fp.getvalue()))
        # This will raise a KeyError if there is no resources.json..
        z.getinfo("resources.json")
