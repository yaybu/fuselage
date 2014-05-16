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
from fuselage.runner import Runner
if __name__=="__main__":
    r = Runner.setup_from_cmdline()
    r.run()
"""


class Builder(object):

    def __init__(self, zfp):
        self.zipfile = zfp

    @classmethod
    def write_to(cls, fp):
        fp.write("#!/usr/bin/env python")
        return cls(zipfile.ZipFile(fp, "w", compression=zipfile.ZIP_DEFLATED))

    @classmethod
    def write_to_path(cls, path):
        return cls.write_to(open(path, "wb"))

    def embed_resource_bundle(self, bundle):
        pass

    def embed_fuselage_runtime(self):
        finder = modulefinder.ModuleFinder()

        finder.load_module(
            fqname="__main__",
            fp=six.StringIO(MAIN_PY),
            pathname="__main__.py",
            file_info=("", "r", modulefinder.imp.PY_SOURCE)
        )

        for name, mod in finder.modules.iteritems():
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
            if "." in name:
                parent = name.rsplit(".", 1)[0]
                code = pkgutil.get_data(parent, basename)
                self.zipfile.writestr(os.path.join(*list(parent.split(".")) + [basename]), code)
            else:
                code = pkgutil.get_data(name, basename)
                self.zipfile.writestr(basename, code)

        self.zipfile.writestr("__main__.py", MAIN_PY)

    def close(self):
        self.zipfile.close()


if __name__ == "__main__":
    b = Builder.write_to_path("example.pex")
    b.embed_fuselage_runtime()
    b.close()
