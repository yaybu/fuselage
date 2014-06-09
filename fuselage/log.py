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
import sys


class LoggerAdapter(logging.LoggerAdapter):

    """
    The upstream LoggerAdapter stops log.info("foo", extra={}) from working.
    This subclass doesnt.
    """

    def log(self, level, msg, *args, **kwargs):
        msg, kwargs = self.process(msg, kwargs)
        self.logger.log(level, msg, *args, **kwargs)

    def isEnabledFor(self, level):
        # Python 3.4 breaks on adapters of adapters, which is lame.
        return self.logger.isEnabledFor(level)

    def process(self, msg, kwargs):
        if not 'extra' in kwargs:
            kwargs['extra'] = {}
        kwargs["extra"].update(self.extra)
        return msg, kwargs


class ResourceFormatter(logging.Formatter):

    """ Automatically add a header and footer to log messages about particular
    resources """

    def format(self, record):
        formatted = logging.Formatter.format(self, record)
        if hasattr(record, "fuselage.diff"):
            formatted = "\n".join((formatted, getattr(record, "fuselage.diff")))
        return formatted


class ConsoleHandler(logging.StreamHandler, object):

    def __init__(self, stream=sys.stdout, level=logging.INFO):
        super(ConsoleHandler, self).__init__(stream)
        self._level = level
        self._resource = None
        self._needs_footer = False
        self._needs_header = False

    def format(self, record):
        prefix = "| " if self._resource else ""
        formatted = super(ConsoleHandler, self).format(record)
        return "\n".join(prefix + line for line in formatted.splitlines())

    def _render_resource_header(self):
        if isinstance(self._resource, str):
            header = self._resource
        else:
            header = self._resource.encode("utf-8")

        rl = len(header)
        if rl < 80:
            total_minuses = 77 - rl
            minuses = int(total_minuses / 2)
            leftover = total_minuses % 2
        else:
            minuses = 4
            leftover = 0

        self.stream.write("/%s %s %s\n" % ("-" * minuses,
                                 header,
                                 "-" * (minuses + leftover)))

        self._needs_header = False
        self._needs_footer = True

    def _render_resource_footer(self):
        self.stream.write("\%s\n\n" % ("-" * 79, ))
        self._needs_footer = False

    def handle(self, record):
        record_type = getattr(record, "fuselage.type", None)
        next_resource = getattr(record, "fuselage.resource", None)

        if record_type == "resource-start":
            self._resource = next_resource
            self._needs_header = True

        if record.levelno >= self._level:
            if self._resource and self._needs_header:
                self._render_resource_header()
            super(ConsoleHandler, self).handle(record)

        if record_type == "resource-finish":
            if self._needs_footer:
                self._render_resource_footer()
            self._resource = None


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


def configure(verbosity=logging.INFO, json=False, force=False):
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    if len(root.handlers) != 0:
        if not force:
            return
        root.handlers[:] = []

    if json:
        root.addHandler(JSONHandler(sys.stdout))
    else:
        handler = ConsoleHandler(sys.stdout, level=verbosity)
        handler.setFormatter(ResourceFormatter())
        root.addHandler(handler)

    #root.addHandler(SysLogHandler())
