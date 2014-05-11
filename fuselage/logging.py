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

from __future__ import absolute_import

import json
import logging
import logging.handlers


class JSONHandler(logging.StreamHandler):

    """
    Output all log info (for specified verbosity) to stdout in JSON. This
    allows parent process to track and report on progress.
    """

    def format(self, record):
        # FIXME: Is implementing a "formatter" enough??
        return json.dumps(record)


class SysLogHandler(logging.handlers.SysLogHandler):

    """
    We output an audit log to syslog. This only contains log entries that are
    marked as changes.
    """

    def filter(self, record):
        if "fuselage.change" not in record.__dict__:
            return 0
        return 1
