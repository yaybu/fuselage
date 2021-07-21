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

import hashlib
import io
import modulefinder
import os
import pkgutil
import zipfile

from fuselage.bundle import ResourceBundle

MAIN_PY = """
import logging
import sys
from fuselage import resources, error, log
from fuselage.runner import BundledRunner
if __name__=="__main__":
    log.configure()
    logger = logging.getLogger("fuselage")
    try:
        r = BundledRunner.setup_from_cmdline()
        r.run()
    except error.Error as e:
        logger.error(e)
        sys.exit(e.returncode)
"""


class Builder:
    def __init__(self, zfp):
        self.zipfile = zfp

    @classmethod
    def write_to(cls, fp):
        fp.write(b"#!/usr/bin/env python3\n")
        obj = cls(zipfile.ZipFile(fp, "w", compression=zipfile.ZIP_DEFLATED))
        obj.fp = fp
        return obj

    @classmethod
    def write_to_path(cls, path):
        return cls.write_to(open(path, "wb"))

    def add_resource_blob(self, payload):
        name = hashlib.sha1(payload).hexdigest()
        self.zipfile.writestr(os.path.join("assets", name), payload)
        return "bundle://" + name

    def embed_resource_bundle(self, bundle: ResourceBundle):
        data = bundle.dumps(self)
        self.zipfile.writestr("resources.json", data)

    def embed_fuselage_runtime(self):
        finder = modulefinder.ModuleFinder()

        co = compile(MAIN_PY, "__main__.py", "exec")
        m = finder.add_module("__main__")
        m.__file__ = "__main__.py"
        finder.scan_code(co, m)

        for name, mod in finder.modules.items():
            if not name.startswith("fuselage"):
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


def build(bundle: ResourceBundle, name: str = "payload.pex") -> io.BytesIO:
    buffer = io.BytesIO()
    buffer.name = name

    bu = Builder.write_to(buffer)
    bu.embed_fuselage_runtime()
    bu.embed_resource_bundle(bundle)
    bu.close()

    buffer.seek(0)
    return buffer
