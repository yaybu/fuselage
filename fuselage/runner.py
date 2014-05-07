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
import logging

from fuselage import error, bundle, event
from fuselage.changes import TextRenderer


logger = logging.getLogger(__name__)


class Runner(object):

    def run(self):
        root = self.root
        self.ypath = root.ypath
        self.resume = root.resume
        self.no_resume = root.no_resume
        self.simulate = root.simulate
        self.verbose = root.verbose

        if not self.simulate and not os.path.exists(self.get_data_path()):
            os.makedirs(self.get_data_path())

        self.state = event.EventState(
            save_file = self.get_data_path("events.saved"),
            simulate = self.simulate,
        )
        self.state.open()

        # Actually apply the configuration
        bundle = bundle.ResourceBundle.create_from_yay_expression(
            self.params.resources, verbose_errors=self.verbose > 2)
        bundle.bind()

        with self.root.ui.throbber("Provision %s" % self.host) as throbber:
            changed = bundle.apply(self, throbber)

        #FIXME: Do we get here if no change has occured??
        self.state.success()

    def change(self, change):
        renderer = TextRenderer.get(change, self.current_output)
        return change.apply(self, renderer)

    def get_file(self, filename, etag=None):
        # FIXME: What does this do now?
        # Does it only work for pex bundles?
        # Does it work standalone?

    def get_data_path(self, path=None):
        if not path:
            return "/var/run/yaybu"
        return os.path.join("/var/run/yaybu", path)
