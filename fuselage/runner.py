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

from fuselage import bundle, event
from fuselage.changes import TextRenderer


logger = logging.getLogger(__name__)


class Runner(object):

    state_path = "/var/run/yaybu"

    def run(self, argv=sys.argv):
        p = optparse.OptionParser
        p.add_option("--simulate", action="store_true")
        p.add_option("--resume", action="store_true")
        p.add_option("--no-resume", action="store_true")
        p.add_option("-v", "--verbose", action="count")
        p.add_option("-q", "--quiet", action="count")
        opts, args = p.parse_args(argv)

        #if len(args) != 1 or args[0] not in ("apply", "test"):
        #    p.print_help()
        #    raise SystemExit(1)

        self.resume = opts.resume
        self.no_resume = opts.no_resume
        self.simulate = opts.simulate
        self.verbose = opts.verbose

        if not self.simulate and not os.path.exists(self.state_path):
            os.makedirs(self.state_path)

        self.state = event.EventState(
            save_file=os.path.join(self.state_path, "events.saved"),
            simulate=self.simulate,
        )
        self.state.open()

        # Actually apply the configuration
        b = bundle.ResourceBundle.create_from_yay_expression(
            self.params.resources, verbose_errors=self.verbose > 2)
        b.bind()
        changed = b.apply(self)

        #FIXME: Do we get here if no change has occured??
        self.state.success()

        return changed

    def change(self, change):
        renderer = TextRenderer.get(change, self.current_output)
        return change.apply(self, renderer)

    def get_file(self, filename, etag=None):
        # FIXME: What does this do now?
        # Does it only work for pex bundles?
        # Does it work standalone?
        pass
