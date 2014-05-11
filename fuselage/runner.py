# Copyright 2012-2014 Isotoma Limited
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

import os
import sys
import logging
import optparse

from fuselage import bundle, error, event
from fuselage import logging as handlers

logger = logging.getLogger(__name__)


class Runner(object):

    state_path = "/var/run/yaybu"

    def __init__(self, resources, resume=False, no_resume=False, simulate=False, verbosity=logging.INFO):
        if self.resume and self.no_resume:
            raise error.ParseError("'resume' and 'no_resume' cannot both be True")

        self.resources = resources
        self.resume = resume
        self.no_resume = no_resume
        self.simulate = simulate
        self.verbosity = verbosity

        self.state = event.EventState(
            save_file=os.path.join(self.state_path, "events.saved"),
            simulate=self.simulate,
        )

    @classmethod
    def setup_from_cmdline(cls, argv=sys.argv):
        p = optparse.OptionParser
        p.add_option("--simulate", action="store_true")
        p.add_option("--resume", action="store_true")
        p.add_option("--no-resume", action="store_true")
        p.add_option("-v", "--verbose", action="count")
        p.add_option("-q", "--quiet", action="count")
        opts, args = p.parse_args(argv)

        resources = bundle.ResourceBundle()

        return cls(
            resources,
            resume=opts.resume,
            no_resume=opts.no_resume,
            simulate=opts.simulate,
            verbosity=logging.INFO + (10 * (opts.verbose - opts.quiet)),
        )

    def configure_logging(self):
        root = logging.getLogger()
        if not sys.stdout.isatty():
            root.addHandler(handlers.JSONHandler(stream=sys.stdout))
        else:
            handler = logging.StreamHandler(stream=sys.stdout)
            root.addHandler(handler)
        root.addHandler(handlers.SysLogHandler())
        root.setLevel(self.verbosity)

    def run(self):
        self.configure_logging()

        if not self.simulate and not os.path.exists(self.state_path):
            os.makedirs(self.state_path)

        self.state.open()

        changed = self.resources.apply(self)

        #FIXME: Do we get here if no change has occured??
        self.state.success()

        return changed
