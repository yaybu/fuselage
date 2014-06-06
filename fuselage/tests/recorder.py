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

import collections
import os
import json
import pkgutil
import logging

from fuselage import error


stat_result = collections.namedtuple("stat_result",
                                     ("st_mode", "st_ino", "st_dev", "st_nlink", "st_uid", "st_gid",
                                      "st_size", "st_atime", "st_mtime", "st_ctime"))

struct_group = collections.namedtuple("struct_group",
                                      ("gr_name", "gr_passwd", "gr_gid", "gr_mem"))

struct_passwd = collections.namedtuple("struct_passwd",
                                       ("pw_name", "pw_passwd", "pw_uid", "pw_gid", "pw_gecos", "pw_dir",
                                        "pw_shell"))

struct_spwd = collections.namedtuple("struct_spwd",
                                     ("sp_nam", "sp_pwd", "sp_lastchg", "sp_min", "sp_max", "sp_warn",
                                      "sp_inact", "sp_expire", "sp_flag", ))

logger = logging.getLogger(__name__)


class Recorder(object):

    def __init__(self, path, id):
        self.path = path
        self.id = id
        self.inner = {}
        self.results = []

    def register(self, function_name, fn):
        self.inner[function_name] = fn

    def __getattr__(self, function_name):
        try:
            attr = self.inner[function_name]
        except KeyError:
            raise AttributeError(function_name)

        def _(*args, **kwargs):
            logger.debug("fuselage.platform.%s(*%r, **%r)" % (function_name, args, kwargs))

            e = None
            try:
                results = attr(*args, **kwargs)
                exception = None
            except KeyError as e:
                results = []
                exception = "KeyError"
            except OSError as e:
                results = []
                exception = "OSError"
            except error.SystemError as e:
                results = [e.returncode, e.stdout, e.stderr]
                exception = "SystemError"
            self.results.append((function_name, results, exception))
            if e:
                raise e
            return results
        return _

    def save(self):
        existing = {}
        if os.path.exists(self.path):
            existing = json.load(open(self.path))
        existing[self.id] = self.results
        with open(self.path, "w") as fp:
            json.dump(existing, fp)


class Player(object):

    def __init__(self, path, id):
        results = {}
        name = os.path.splitext(os.path.basename(path))[0]
        payload = pkgutil.get_data("fuselage.tests", "%s.json" % (name, ))
        if payload:
            results.update(json.loads(payload.decode()))

        self.results = results.get(id, [])
        logger.debug("Loaded %d results from cassette %r" % (len(self.results), id))

    def register(self, function_name, fn):
        pass

    def __getattr__(self, function_name):
        def _(*args, **kwargs):
            f, results, exception = self.results.pop(0)
            assert function_name == f, "'%s' != '%s', args=%r, kwargs=%r" % (function_name, f, args, kwargs)

            logger.debug("fuselage.platform.%s(*%r, **%r)" % (function_name, args, kwargs))

            if exception:
                raise {
                    "KeyError": KeyError,
                    "OSError": OSError,
                    "SystemError": error.SystemError,
                }[exception](*results)
            return {
                "stat": lambda x: stat_result(*x),
                "lstat": lambda x: stat_result(*x),
                "getgrall": lambda x: [struct_group(*y) for y in x],
                "getgrnam": lambda x: struct_group(*x),
                "getgrgid": lambda x: struct_group(*x),
                "getpwall": lambda x: [struct_passwd(*y) for y in x],
                "getpwnam": lambda x: struct_passwd(*x),
                "getpwuid": lambda x: struct_passwd(*x),
                "getspall": lambda x: [struct_spwd(*y) for y in x],
                "getspnam": lambda x: struct_spwd(*x),
            }.get(f, lambda x: x)(results)
        return _

    def save(self):
        # Player doesn't change anything, so this is a no-op
        return
