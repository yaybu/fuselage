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

import six
from fuselage import error


class PolicyType(type):

    """ Registers the policy on the resource """

    def __new__(meta, class_name, bases, new_attrs):
        cls = type.__new__(meta, class_name, bases, new_attrs)
        cls.providers = []
        if getattr(cls, "resource", None) is not None:
            cls.resource.policies[cls.name] = cls
        return cls


class Policy(six.with_metaclass(PolicyType)):

    """
    A policy is a representation of a resource. A policy requires a
    certain argument signature to be present before it can be used. There may
    be multiple policies selected for a resource, in which case all argument
    signatures must be conformant.

    Providers must provide all selected policies to be a valid provider for
    the resource.
    """

    # specify true if you wish this policy to be enabled by default
    default = False
    # the name of the policy, used to find it in the ensures config
    name = None
    # specify the resource to which this policy applies
    resource = None
    # the list of providers that provide this policy
    providers = []
    # Override this with a list of assertions
    signature = ()

    def __init__(self, resource):
        self.resource = resource

    @classmethod
    def conforms(self, resource):
        """ Test if the provided resource conforms to the signature for this
        policy. """
        return AND(*self.signature).test(resource)

    @classmethod
    def validate(self, resource):
        a = AND(*self.signature)
        if a.test(resource):
            return

        msg = [
            "The resource '%s' is using the policy '%s' but doesn't confirm to that policy" %
            (resource, self.name), ""]
        msg.extend(a.describe(resource))
        raise error.NonConformingPolicy("\n".join(msg))

    def get_provider(self):
        """ Get the one and only one provider that is valid for this resource,
        policy and overall context """
        import fuselage.providers  # noqa
        valid = [p.isvalid(self, self.resource) for p in self.providers]
        if valid.count(True) > 1:
            raise error.TooManyProviders()
        if valid.count(True) == 0:
            raise error.NoSuitableProviders()
        return self.providers[valid.index(True)]


class NullPolicy(Policy):
    pass


class ArgumentAssertion(object):

    """ An assertion of the state of an argument """

    def __init__(self, name):
        self.name = name


class Present(ArgumentAssertion):

    """ The argument has been specified, or has a default value. """

    def test(self, resource):
        """ Test that the argument this asserts for is present in the
        resource. """
        if getattr(resource, self.name) is not None:
            return True

    def describe(self, resource):
        yield "'%s' must be present (%s)" % (self.name, self.test(resource))


class Absent(ArgumentAssertion):

    """ The argument has not been specified by the user and has no default
    value. An argument with a default value is always defined. """

    def test(self, resource):
        val = getattr(resource, self.name)
        if val is None:
            return True
        if val == resource.__defaults__[self.name]:
            return True
        return False

    def describe(self, resource):
        yield "'%s' must be absent (%s)" % (self.name, self.test(resource))


class AND(ArgumentAssertion):

    def __init__(self, *args):
        self.args = args

    def test(self, resource):
        for a in self.args:
            if not a.test(resource):
                return False
        return True

    def describe(self, resource):
        yield "The follow conditions must all be met:"
        for a in self.args:
            for msg in a.describe(resource):
                yield "  " + msg
        yield ""


class NAND(ArgumentAssertion):

    def __init__(self, *args):
        self.args = args

    def test(self, resource):
        results = [1 for a in self.args if a.test(resource)]
        if len(results) > 1:
            return False
        return True

    def describe(self, resource):
        yield "No more than 1 of the following conditions should be true:"
        for a in self.args:
            for msg in a.describe(resource):
                yield "  " + msg
        yield ""


class XOR(ArgumentAssertion):

    def __init__(self, *args):
        self.args = args

    def test(self, resource):
        l = [1 for a in self.args if a.test(resource)]
        if len(l) == 0:
            return False
        elif len(l) == 1:
            return True
        else:
            return False

    def describe(self, resource):
        yield "Only one of the following conditions should be true:"
        for a in self.args:
            for msg in a.describe(resource):
                yield "  " + msg
        yield ""


class OR(ArgumentAssertion):

    def __init__(self, *args):
        self.args = args

    def test(self, resource):
        l = [1 for a in self.args if a.test(resource)]
        if len(l) == 0:
            return False
        else:
            return True

    def describe(self, resource):
        yield "At least one of the following conditions should be true:"
        for a in self.args:
            for msg in a.describe(resource):
                yield "  " + msg
        yield ""
