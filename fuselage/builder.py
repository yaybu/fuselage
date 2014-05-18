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
import modulefinder
import os
import pkgutil
import zipfile


MAIN_PY = """
from fuselage import resources
from fuselage.runner import BundledRunner
if __name__=="__main__":
    r = BundledRunner.setup_from_cmdline()
    r.run()
"""


class Builder(object):

    def __init__(self, zfp):
        self.zipfile = zfp

    @classmethod
    def write_to(cls, fp):
        fp.write(b"#!/usr/bin/env python\n")
        return cls(zipfile.ZipFile(fp, "w", compression=zipfile.ZIP_DEFLATED))

    @classmethod
    def write_to_path(cls, path):
        return cls.write_to(open(path, "wb"))

    def add_resource(self, name, payload):
        self.zipfile.writestr(os.path.join("assets", name), payload)

    def embed_resource_bundle(self, bundle):
        data = bundle.dumps(self)
        self.zipfile.writestr("resources.json", data)

    def embed_fuselage_runtime(self):
        finder = modulefinder.ModuleFinder()

        finder.load_module(
            fqname="__main__",
            fp=six.StringIO(MAIN_PY),
            pathname="__main__.py",
            file_info=("", "r", modulefinder.imp.PY_SOURCE)
        )

        for name, mod in finder.modules.items():
            mods = ("fuselage", "six")
            for m in mods:
                if name.startswith(m):
                    break
            else:
                continue

            if name.startswith("fuselage.tests."):
                continue

            # Use pkgutil to get the code - this is zipsafe so will work even if
            # running from a py2exe type binary installation.
            basename = os.path.basename(mod.__file__)
            path_parts = out_parts = list(name.split("."))
            if basename == "__init__.py":
                path_parts.append("__init__.py")
            elif not "." in name:
                path_parts = [name, name + ".py"]
                out_parts = [name + ".py"]
            else:
                path_parts[-1] += ".py"

            code = pkgutil.get_data(path_parts[0], os.sep.join(path_parts[1:]))
            self.zipfile.writestr(os.path.join(*out_parts), code)

        self.zipfile.writestr("__init__.py", "")
        self.zipfile.writestr("__main__.py", MAIN_PY)

    def close(self):
        self.zipfile.close()


if __name__ == "__main__":
    from .bundle import ResourceBundle
    b = Builder.write_to_path("example.pex")
    b.embed_fuselage_runtime()
    b.embed_resource_bundle(ResourceBundle())
    b.close()
