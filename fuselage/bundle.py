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

import json
import logging

from fuselage import error, log
from fuselage.resource import ResourceType


logger = logging.getLogger(__name__)


class ResourceBundle(object):

    """ An ordered, indexed collection of resources. Pass in a specification
    that consists of scalars, lists and dictionaries and this class will
    instantiate the appropriate resources into the structure. """

    BUNDLE_VERSION = 1

    def __init__(self):
        self.clear()

    @classmethod
    def from_iterator(cls, iterator):
        bun = cls()
        if iterator:
            bun.extend(iterator)
        return bun

    def __len__(self):
        return len(self.resources)

    def __getitem__(self, key):
        return self._index_by_id[key]

    def clear(self):
        self.resources = []
        self._index_by_id = {}

    def get_resource_by_name(self, target):
        for res in self.resources:
            if res.id == target:
                return res
        else:
            raise KeyError("No such resource by name '%s'" % target)

    def dump(self, builder, fp):
        obj = self._serialize_bundle(builder)
        json.dump(obj, fp)

    def dumps(self, builder):
        obj = self._serialize_bundle(builder)
        return json.dumps(obj)

    def _serialize_bundle(self, builder):
        obj = {"version": self.BUNDLE_VERSION}
        resources = obj['resources'] = []
        for r in self.resources:
            if not getattr(r, "_implicit", False):
                resources.append(r.serialize(builder))
        return obj

    def load(self, fp):
        obj = json.load(fp)
        return self._load_bundle(obj)

    def loads(self, s):
        obj = json.loads(s)
        return self._load_bundle(obj)

    def _load_bundle(self, obj):
        if not isinstance(obj, dict):
            raise error.ParseError("Bundle is not a dictionary")

        if 'version' not in obj:
            raise error.ParseError("Bundle version is invalid")

        if obj['version'] > self.BUNDLE_VERSION:
            raise error.ParseError("Bundle version is too new")

        if "resources" not in obj:
            raise error.ParseError("Bundle doesn't have a resources key")

        if not isinstance(obj["resources"], list):
            raise error.ParseError("Bundle's resource list is not a list")

        for resource in obj["resources"]:
            if not isinstance(resource, dict):
                raise error.ParseError("Not a valid resource definition")

            if len(resource) != 1:
                raise error.ParseError("Wrong number of keys in outer resource definition")

            typename = list(resource.keys())[0]
            instances = resource[typename]
            if isinstance(instances, dict):
                instances = [instances]

            for instance in instances:
                self.create(typename, **instance)

    def create(self, typename, **kwargs):
        try:
            kls = ResourceType.resources[typename]
        except KeyError:
            raise error.ParseError("There is no resource type of '%s'" % typename)

        resource = kls(**kwargs)

        return self.add(resource)

    def add(self, resource):
        if resource.typed_id in self._index_by_id:
            raise error.ParseError("Resources cannot be defined multiple times")

        # Create implicit File[] nodes for any watched files
        for watched in resource.changes:
            w = self.create("File", **{
                "name": watched,
                "policy": "watched",
            })
            w._original_hash = None
            w._implicit = True

        resource.bind(self)
        self.resources.append(resource)
        self._index_by_id[resource.typed_id] = resource
        return resource

    def extend(self, iterator):
        while True:
            try:
                resource = next(iterator)
            except StopIteration:
                break

            try:
                self.add(resource)
            except Exception as e:
                throw = getattr(iterator, 'throw', None)
                if callable(throw):
                    throw(e)
                else:
                    raise

    def apply(self, runner):
        """ Apply the resources to the system, using the provided context and
        overall configuration. """
        for resource in self.resources:
            if hasattr(resource, "_original_hash"):
                resource._original_hash = resource.hash()

        something_changed = False
        mylen = len(self.resources)
        for i, resource in enumerate(self.resources, start=1):
            resource_log = log.LoggerAdapter(logger, {
                "fuselage.resource": resource.typed_id,
            })

            resource_log.debug("Started applying '%r' (%d of %d)" % (resource, i, mylen), extra={"fuselage.type": "resource-start"})
            try:
                if resource.apply(runner):
                    resource_log.debug("'%r' made changes" % (resource, ))
                    something_changed = True
            finally:
                resource_log.debug("Finished applying '%r'" % (resource, ), extra={"fuselage.type": "resource-finish"})

        if not something_changed:
            raise error.NothingChanged()
