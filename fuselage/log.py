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


class LoggerAdapter(logging.LoggerAdapter):

    """
    The upstream LoggerAdapter stops log.info("foo", extra={}) from working.
    This subclass doesnt.
    """

    def process(self, msg, kwargs):
        if not 'extra' in kwargs:
            kwargs['extra'] = {}
        kwargs["extra"].update(self.extra)
        return msg, kwargs


class ResourceFormatter(logging.Formatter):

    """ Automatically add a header and footer to log messages about particular
    resources """

    def __init__(self, *args):
        logging.Formatter.__init__(self, *args)
        self.resource = None

    def format(self, record):
        next_resource = getattr(record, "fuselage.resource", None)

        rv = u""

        # Is the logging now about a different resource?
        if next_resource and self.resource != next_resource:

            # If there was already a resource, let us add a footer
            if self.resource:
                rv += self.render_resource_footer()

            self.resource = next_resource

            # Are we now logging for a new resource?
            if self.resource:
                rv += self.render_resource_header()

        formatted = logging.Formatter.format(self, record)

        if hasattr(record, "fuselage.diff"):
            formatted = "\n".join((formatted, getattr(record, "fuselage.diff")))

        if self.resource:
            rv += "\r\n".join("| %s" % line for line in formatted.splitlines()) + "\r"
        else:
            rv += formatted

        return rv

    def render_resource_header(self):
        header = self.resource

        rl = len(header)
        if rl < 80:
            total_minuses = 77 - rl
            minuses = int(total_minuses / 2)
            leftover = total_minuses % 2
        else:
            minuses = 4
            leftover = 0

        return u"/%s %s %s\n" % ("-" * minuses,
                                 header,
                                 "-" * (minuses + leftover))

    def render_resource_footer(self):
        return u"\%s\n\n" % ("-" * 79,)


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
