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

import logging
import unittest

from fuselage import bundle, error, runner


class TestRunner(unittest.TestCase):

    def test_init(self):
        r = runner.Runner(bundle.ResourceBundle())
        self.assertEqual(r.simulate, False)
        self.assertEqual(r.state.simulate, False)

    def test_setup_from_cmdline__increase_verbosity(self):
        r = runner.Runner.setup_from_cmdline(["-v"])
        self.assertEqual(r.verbosity, logging.DEBUG)

    def test_setup_from_cmdline__decrease_verbosity(self):
        r = runner.Runner.setup_from_cmdline(["-q"])
        self.assertEqual(r.verbosity, logging.WARNING)

    def test_setup_from_cmdline__enable_simulate(self):
        r = runner.Runner.setup_from_cmdline(["-s"])
        self.assertEqual(r.simulate, True)
        self.assertEqual(r.state.simulate, True)

    def test_resume_and_not_resume(self):
        self.assertRaises(error.ParseError, runner.Runner, [], resume=True, no_resume=True)
