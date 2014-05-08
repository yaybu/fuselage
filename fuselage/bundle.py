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

import collections
try:
    from collections import OrderedDict
except ImportError:
    from fuselage.ordereddict import OrderedDict

from fuselage.argument import Property, List, PolicyArgument, String
from fuselage import policy
from fuselage import error
from fuselage.resource import ResourceType


class ResourceBundle(OrderedDict):

    """ An ordered, indexed collection of resources. Pass in a specification
    that consists of scalars, lists and dictionaries and this class will
    instantiate the appropriate resources into the structure. """

    @classmethod
    def create_from_list(cls, specification):
        """ Given a list of types and parameters, build a resource bundle """
        c = Config()
        c.add({"resources": specification})
        return cls.create_from_yay_expression(c.resources)

    def key_remap(self, kw):
        """ Maps - to _ to make resource attribute name more pleasant. """
        for k, v in kw.items():
            k = k.replace("-", "_")
            yield str(k), v

    def add_from_node(self, spec):
        try:
            spec.as_dict()
        except errors.TypeError:
            raise error.ParseError("Not a valid Resource definition", anchor=spec.anchor)

        keys = list(spec.keys())
        if len(keys) > 1:
            raise error.ParseError("Too many keys in list item", anchor=spec.anchor)

        typename = keys[0]
        instances = spec.get_key(typename)

        try:
            instances.as_dict()
            iterable = [instances]
        except errors.TypeError:
            iterable = instances.get_iterable()

        for instance in iterable:
            self.add(typename, instance)

    def add(self, typename, instance):
        if not hasattr(instance, "keys"):
            raise error.ParseError("Expected mapping for %s" % typename, anchor=getattr(instance, "anchor", None))

        try:
            kls = ResourceType.resources[typename]
        except KeyError:
            raise error.ParseError(
                "There is no resource type of '%s'" % typename, anchor=instance.anchor)

        resource = kls(instance)
        if resource.id in self:
            raise error.ParseError(
                "'%s' cannot be defined multiple times" % resource.id, anchor=instance.anchor)

        self[resource.id] = resource

        # Create implicit File[] nodes for any watched files
        try:
            for watched in resource.watch:
                res = bind({
                    "name": watched,
                    "policy": "watched",
                })
                res.parent = instance
                w = self.add("File", res)
                w._original_hash = None
        except errors.NoMatching:
            pass

        return resource

    def bind(self):
        """ Bind all the resources so they can observe each others for policy
        triggers. """
        for i, resource in enumerate(self.values()):
            for bound in resource.bind(self):
                if bound == resource:
                    raise error.BindingError(
                        "Attempt to bind %r to itself!" % resource)
                j = self.values().index(bound)
                if j > i:
                    raise error.BindingError(
                        "Attempt to bind forwards on %r" % resource)

    def test(self, ctx):
        for resource in self.values():
            resource.validate(ctx)
            resource.test(ctx)

    def apply(self, ctx, throbber):
        """ Apply the resources to the system, using the provided context and
        overall configuration. """
        for resource in self.values():
            resource.validate(ctx)
            if hasattr(resource, "_original_hash"):
                resource._original_hash = resource.hash(ctx)

        throbber.set_upper(len(self.values()))
        something_changed = False
        for i, resource in enumerate(self.values(), start=1):
            with throbber.section(resource.id) as output:
                ctx.current_output = output
                if resource.apply(ctx, output):
                    something_changed = True
                ctx.current_output = None
            throbber.set_current(i)

        return something_changed
