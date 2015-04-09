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

import logging
import six

from fuselage.argument import Argument, List, SubscriptionArgument, PolicyArgument, String
from fuselage import policy, error, log
from fuselage.utils import force_str

logger = logging.getLogger(__name__)


class ResourceType(type):

    """ Keeps a registry of resources as they are created, and provides some
    simple access to their arguments. """

    resources = {}

    def __new__(meta, class_name, bases, new_attrs):
        new_attrs.setdefault("__resource_name__", class_name)
        cls = type.__new__(meta, class_name, bases, new_attrs)

        cls.__args__ = {}

        for b in bases:
            if hasattr(b, "__args__"):
                cls.__args__.update(b.__args__)

        cls.policies = AvailableResourcePolicies()

        if class_name != 'Resource':
            if cls.__resource_name__ in meta.resources:
                raise error.ParseError("Redefinition of resource %s" % cls.__resource_name__)
            else:
                meta.resources[cls.__resource_name__] = cls

        for key, value in new_attrs.items():
            if isinstance(value, Argument):
                cls.__args__[key] = value

        return cls

    @classmethod
    def clear(self):
        self.resources = {}


class AvailableResourcePolicies(dict):

    """ A collection of the policies available for a resource, with some logic
    to work out which of them is the one and only default policy. """

    def default(self):
        default = [p for p in self.values() if p.default]
        if default:
            return default[0]
        else:
            return policy.NullPolicy


class Resource(six.with_metaclass(ResourceType)):

    """ A resource represents a resource that can be configured on the system.
    This might be as simple as a symlink or as complex as a database schema
    migration. Resources have policies that represent how the resource is to
    be treated. Providers are the implementation of the resource policy.

    Resource definitions specify the complete set of attributes that can be
    configured for a resource. Policies define which attributes must be
    configured for the policy to be used.

    """

    policies = AvailableResourcePolicies()
    """ A dictionary of policy names mapped to policy classes (not objects).

    These are the policies for this resource class.

    Here be metaprogramming magic.

    Dynamically allocated as Yaybu starts up this is effectively static once
    we're up and running. The combination of this attribute and the policy
    argument below is sufficient to determine which provider might be
    appropriate for this resource.

    """

    policy = PolicyArgument()
    """ The list of policies provided by configuration. This is an argument
    like any other, but has a complex representation that holds the conditions
    and options for the policies as specified in the input file. """

    id = String(default=lambda r: r.implicit_id)

    watches = SubscriptionArgument()

    changes = List(default=[])
    """ A list of files to monitor while this resource is applied

    The file will be hashed before and after a resource is applied.
    If the hash changes, then it will be like a policy has been applied
    on that file.

    For example::

        resources.append:
          - Execute:
              name: buildout-foobar
              command: buildout2.6
              watch:
                - /var/local/sites/foobar/apache/apache.cfg

          - Service:
              name: apache2
              policy:
                restart:
                  when: watched
                  on: File[/var/local/sites/foobar/apache/apache.cfg]
    """

    def __init__(self, **kwargs):
        """ Takes a reference to a Yay AST node """
        self.observers = list()

        for key, value in kwargs.items():
            if key not in self.__args__:
                raise error.ParseError("'%s' is not a valid option for this resource" % (key, ))
            setattr(self, key, value)

        self.policy.validate()
        self.policy.get_provider()

        if not self.id:
            raise error.ParseError((
                "{0} is not explicitly named and name cannot be implied").format(
                    self.__resource_name__
            ))

    @classmethod
    def get_argument_names(klass):
        for key in klass.__args__:
            yield key

    def serialize(self, builder=None):
        """ Return all argument names and values in a dictionary. If an
        argument has no default and has not been set, it's value in the
        dictionary will be None. """
        retval = {}
        for name, arg in self.__args__.items():
            if arg.present(self):
                retval[name] = arg.serialize(self, builder=builder)
        return {self.__resource_name__: retval}

    def register_observer(self, when, resource, policy):
        logger.debug("%r is being observed by %r for %s" % (self, resource, when))
        self.observers.append(resource)

    def apply(self, runner):
        """ Apply the provider for the selected policy, and then fire any
        events that are being observed. """

        l = log.LoggerAdapter(logger, {"fuselage.resource": self.id})

        if self.watches and not runner.state.is_trigger_set(self):
            l.debug("Skipping resource apply as subscribed to triggers that are not set")
            return False

        provider = self.policy.get_provider()(self, runner)
        changed = provider.apply()
        runner.state.unset_trigger(self)
        if changed:
            self.fire_event(runner)
        return changed

    def fire_event(self, context):
        """ Apply the appropriate policies on the resources that are observing
        this resource for the firing of a policy. """
        logger.debug("Sending triggers from %s" % (self, ))
        for resource in self.observers:
            logger.debug("Sending trigger from %r to %r" % (self, resource, ))
            context.state.set_trigger(resource)

    def bind(self, resources):
        """ Bind this resource to all the resources on which it triggers.
        Returns a list of the resources to which we are bound. """
        bound = []
        if self.watches:
            for trigger in self.watches:
                bound.append(trigger.bind(resources, self))
        return bound

    @property
    def implicit_id(self):
        if getattr(self, "name", None):
            return force_str(self.name)
        return None

    @property
    def typed_id(self):
        name = self.id
        if not name:
            raise error.ParseError("Resource is not named")
        classname = getattr(self, '__resource_name__', self.__class__.__name__)
        return "%s[%s]" % (classname, name)

    def __repr__(self):
        return self.typed_id
