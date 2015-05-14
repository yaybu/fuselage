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

from fuselage import platform


def get_default_user():
    if not platform.getpwuid:
        return ""
    return platform.getpwuid(platform.getuid()).pw_name


def get_default_group(user):
    if not platform.getpwnam:
        return ""
    try:
        gid = platform.getpwnam(user).pw_gid
        return platform.getgrgid(gid).gr_name
    except KeyError:
        return None
