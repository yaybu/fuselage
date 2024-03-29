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

import re
import unicodedata


def force_str(s):
    if isinstance(s, str):
        return s
    elif isinstance(s, bytes):
        return s.decode("utf-8")
    raise ValueError("Not a string")


def force_unicode(s):
    if isinstance(s, bytes):
        return s.decode("utf-8")
    elif isinstance(s, str):
        return s
    raise ValueError("Not a string")


def force_bytes(s):
    if isinstance(s, bytes):
        return s
    elif isinstance(s, str):
        return s.encode("utf-8")
    raise ValueError("Not a string")


def simple_str(s):
    """'Normalize' a string - lowercase, strip unicode, replace whitespace, etc"""
    s = force_str(
        unicodedata.normalize("NFKD", force_unicode(s)).encode("ascii", "ignore")
    )
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s)
    return s
