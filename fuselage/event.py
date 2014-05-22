# Copyright 2011-2014 Isotoma Limited
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
import json

from fuselage import error


class EventState(object):

    """
    Represents the current state of events

    Createw a JSON state file on the target system. fuselage is idempotent - it
    doesn't rely on this to know if it's applied your changes. It relies on it
    on it to keep track of watch triggers.

    For example, if you make a change to a File, fuselage doesn't need this
    state data to make sure the file is updated. But if you have an Execute
    that watches the File then this state date will ensure the Execute is
    trigger when resuming from failure.
    """

    overrides = {}
    """ A mapping of resource ids to the overridden policy name for that
    resource, if there is one. """

    def __init__(self, save_file, simulate, load=False):
        self.save_file = save_file
        self.simulate = simulate
        self.loaded = not load
        self.overrides = {}
        self.simulate = simulate

    def load(self):
        if self.loaded:
            return
        if os.path.exists(self.save_file):
            with open(self.save_file, "r") as fp:
                self.overrides = json.load(fp)
        self.loaded = True

    def set_trigger(self, resource):
        self.load()
        self.overrides[resource.id] = '*'
        self.save()

    def unset_trigger(self, resource):
        self.load()
        if resource.id in self.overrides:
            del self.overrides[resource.id]
            self.save()

    def is_trigger_set(self, resource):
        self.load()
        return resource.id in self.overrides

    def open(self):
        if not self.simulate:
            save_parent = os.path.realpath(
                os.path.join(self.save_file, os.path.pardir))
            if not os.path.exists(save_parent):
                os.makedirs(save_parent)

        if not os.path.exists(self.save_file):
            return

        if self.resume:
            self.loaded = False
        elif self.no_resume:
            if not self.simulate:
                os.unlink(self.save_file)
            self.loaded = True

        raise error.SavedEventsAndNoInstruction()

    def success(self):
        if not self.simulate and os.path.exists(self.save_file):
            os.unlink(self.save_file)

    def save(self):
        if not self.simulate:
            with open(self.save_file, "w") as fp:
                json.dump(self.overrides, fp)
