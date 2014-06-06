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
import pkgutil

from fuselage import bundle, error, event, platform

logger = logging.getLogger(__name__)


class Runner(object):

    state_path = "/var/run/yaybu"

    def __init__(self, resources, resume=False, no_resume=False, simulate=False, verbosity=None):
        if resume and no_resume:
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
    def get_resources(cls):
        return bundle.ResourceBundle()

    @classmethod
    def setup_from_cmdline(cls, argv=sys.argv, resources=None):
        p = optparse.OptionParser()
        p.add_option("-s", "--simulate", action="store_true", default=False)
        p.add_option("--resume", action="store_true", default=False)
        p.add_option("--no-resume", action="store_true", default=False)
        p.add_option("-v", "--verbose", action="count", default=0)
        p.add_option("-q", "--quiet", action="count", default=0)
        opts, args = p.parse_args(argv)

        return cls(
            resources or cls.get_resources(),
            resume=opts.resume,
            no_resume=opts.no_resume,
            simulate=opts.simulate,
            verbosity=logging.INFO - (10 * (opts.verbose - opts.quiet)),
        )

    def run(self):
        #if self.verbosity is not None:
        #    logging.getLogger().setLevel(self.verbosity)

        logger.debug("Runner started")
        logger.debug("Created runner with %d resources" % len(self.resources))

        if not self.simulate and not platform.exists(self.state_path):
            logger.debug("Creating state directories at %r" % self.state_path)
            platform.makedirs(self.state_path)

        self.state.open()

        changed = self.resources.apply(self)

        #FIXME: Do we get here if no change has occured??
        self.state.success()

        return changed


class BundledRunner(Runner):

    @classmethod
    def get_resources(self):
        loader = pkgutil.get_loader("fuselage")
        try:
            resources_json = loader.get_data("resources.json")
        except IOError:
            raise error.ParseError("Bundle is missing resources.json")
        b = bundle.ResourceBundle()
        b.loads(resources_json)
        return b
