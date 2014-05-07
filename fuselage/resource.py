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

from fuselage.argument import Property, List, PolicyArgument, String
from fuselage import policy
from fuselage import error
from fuselage.ordereddict import OrderedDict


class ResourceType(type):

    """ Keeps a registry of resources as they are created, and provides some
    simple access to their arguments. """

    resources = {}

    def __new__(meta, class_name, bases, new_attrs):
        cls = type.__new__(meta, class_name, bases, new_attrs)

        cls.policies = AvailableResourcePolicies()

        if class_name != 'Resource':
            rname = new_attrs.get("__resource_name__", class_name)
            if rname in meta.resources:
                raise error.ParseError("Redefinition of resource %s" % rname)
            else:
                meta.resources[rname] = cls

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


class Resource(object):

    """ A resource represents a resource that can be configured on the system.
    This might be as simple as a symlink or as complex as a database schema
    migration. Resources have policies that represent how the resource is to
    be treated. Providers are the implementation of the resource policy.

    Resource definitions specify the complete set of attributes that can be
    configured for a resource. Policies define which attributes must be
    configured for the policy to be used.

    """

    __metaclass__ = ResourceType

    policies = AvailableResourcePolicies()
    """ A dictionary of policy names mapped to policy classes (not objects).

    These are the policies for this resource class.

    Here be metaprogramming magic.

    Dynamically allocated as Yaybu starts up this is effectively static once
    we're up and running. The combination of this attribute and the policy
    argument below is sufficient to determine which provider might be
    appropriate for this resource.

    """

    policy = Property(PolicyArgument)
    """ The list of policies provided by configuration. This is an argument
    like any other, but has a complex representation that holds the conditions
    and options for the policies as specified in the input file. """

    name = Property(String)

    watch = Property(List, default=[])
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

    def __init__(self, inner):
        """ Takes a reference to a Yay AST node """
        self.inner = PythonicWrapper(inner)
        self.inner.parent = inner.parent
        self.observers = collections.defaultdict(list)

        for k in dir(self):
            prop = getattr(self, k)
            if isinstance(prop, Property):
                i = getattr(self.inner, k)
                i.inner.parent = inner.parent
                i.parent = inner.parent
                p = prop.klass(self, i, **prop.kwargs)
                setattr(self, k, p)

    @classmethod
    def get_argument_names(klass):
        for k in dir(klass):
            attr = getattr(klass, k)
            if isinstance(attr, Property):
                yield k

    def get_argument_values(self):
        """ Return all argument names and values in a dictionary. If an
        argument has no default and has not been set, it's value in the
        dictionary will be None. """

        retval = {}
        for key in self.get_argument_names():
            retval[key] = getattr(self, key, None)

    def register_observer(self, when, resource, policy):
        self.observers[when].append((resource, policy))

    def validate(self, context):
        """ Validate that this resource is correctly specified. Will raise
        an exception if it is invalid. Returns True if it is valid.

        We only validate if:

           - only known arguments are specified
           - the chosen policies all exist, or
           - there is at least one default policy, and
           - the arguments provided conform with all selected policies, and
           - the selected policies all share a single provider

        If the above is all true then we can identify a provider that should
        be able to implement the required policies.

        """

        # This will throw any error if any of our validation fails
        self.get_argument_values()

        # Only allow keys that are in the schema
        for key in self.inner.keys():
            if key not in self.get_argument_names():
                raise error.ParseError(
                    "'%s' is not a valid option for resource %s" % (key, self),
                    self.inner.anchor)

        # Error if doesn't conform to policy
        for p in self.get_potential_policies():
            p.validate(self)

            # throws an exception if there is not oneandonlyone provider
            p.get_provider(context)

        return True

    def test(self, context):
        """ Apply the provider for the selected policy, and then fire any
        events that are being observed. """
        for policy in self.get_potential_policies():
            Provider = policy.get_provider(context)
            p = Provider(self)
            p.test(context)

    def apply(self, context, output=None, policy=None):
        """ Apply the provider for the selected policy, and then fire any
        events that are being observed. """
        if policy is None:
            pol = self.get_default_policy(context)
        else:
            pol_class = self.policies[policy]
            pol = pol_class(self)
        prov_class = pol.get_provider(context)
        prov = prov_class(self)
        changed = prov.apply(context, output)
        context.state.clear_override(self)
        if changed:
            self.fire_event(context, pol.name)
        return changed

    def fire_event(self, context, name):
        """ Apply the appropriate policies on the resources that are observing
        this resource for the firing of a policy. """
        for resource, policy in self.observers[name]:
            context.state.override(resource, policy)

    def bind(self, resources):
        """ Bind this resource to all the resources on which it triggers.
        Returns a list of the resources to which we are bound. """
        bound = []
        policy = self.policy.resolve()
        if policy:
            for trigger in policy.triggers:
                bound.append(trigger.bind(resources, self))
        return bound

    def get_potential_policies(self):
        policy = self.policy.resolve()
        if policy:
            return [P(self) for P in policy.all_potential_policies(self)]
        else:
            return [self.policies.default()(self)]

    def get_default_policy(self, context):
        """ Return an instantiated policy for this resource. """
        selected = context.state.overridden_policy(self)
        if not selected:
            policy = self.policy.resolve()
            if policy:
                selected = policy.literal_policy(self)
            else:
                selected = self.policies.default()
        return selected(self)

    @property
    def id(self):
        classname = getattr(self, '__resource_name__', self.__class__.__name__)
        return "%s[%s]" % (classname, self.inner.name.as_string())

    def __repr__(self):
        return self.id
