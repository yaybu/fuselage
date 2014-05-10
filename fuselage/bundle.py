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

try:
    from collections import OrderedDict
except ImportError:
    from fuselage.ordereddict import OrderedDict

from fuselage import error
from fuselage.resource import ResourceType


class ResourceBundle(OrderedDict):

    """ An ordered, indexed collection of resources. Pass in a specification
    that consists of scalars, lists and dictionaries and this class will
    instantiate the appropriate resources into the structure. """

    @classmethod
    def create_from_list(cls, specification):
        """ Given a list of types and parameters, build a resource bundle """
        raise NotImplementedError(cls.create_from_list)

    def key_remap(self, kw):
        """ Maps - to _ to make resource attribute name more pleasant. """
        for k, v in kw.items():
            k = k.replace("-", "_")
            yield str(k), v

    def add_from_node(self, spec):
        if not isinstance(spec, dict):
            raise error.ParseError("Not a valid Resource definition")

        keys = list(spec.keys())
        if len(keys) > 1:
            raise error.ParseError("Too many keys in list item")

        typename = keys[0]
        instances = spec[typename]

        if isinstance(instances, dict):
            iterable = [instances]
        else:
            iterable = instances

        for instance in iterable:
            self.add(typename, instance)

    def add_from_dict(self, typename, instance):
        if not hasattr(instance, "keys"):
            raise error.ParseError("Expected dict for %s" % typename)

        try:
            kls = ResourceType.resources[typename]
        except KeyError:
            raise error.ParseError("There is no resource type of '%s'" % typename)

        resource = kls(instance)

        # Create implicit File[] nodes for any watched files
        for watched in resource.watch:
            w = self.add("File", {
                "name": watched,
                "policy": "watched",
            })
            w._original_hash = None

        return resource

    def add(self, resource):
        if resource.id in self:
            raise error.ParseError("Resources cannot be defined multiple times")

        for bound in resource.bind(self):
            if bound == resource:
                raise error.BindingError("Resources cannot bind to themselves")

        self[resource.id] = resource

    def apply(self, runner):
        """ Apply the resources to the system, using the provided context and
        overall configuration. """
        for resource in self.values():
            if hasattr(resource, "_original_hash"):
                resource._original_hash = resource.hash(runner)

        something_changed = False
        for i, resource in enumerate(self.values(), start=1):
            if resource.apply(runner):
                something_changed = True

        return something_changed
