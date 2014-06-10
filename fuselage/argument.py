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
import sys
from abc import ABCMeta, abstractmethod
import random

from fuselage import error
from fuselage.utils import force_str


class Argument(object):

    """ Stores the argument value on the instance object. It's a bit fugly,
    neater ways of doing this that do not involve passing extra arguments to
    Argument are welcome. """

    metaclass = ABCMeta
    argument_id = 0
    default = None

    def __init__(self, **kwargs):
        self.default = kwargs.pop("default", self.default)
        self.__doc__ = kwargs.pop("help", None)
        self.arg_id = "argument_%d" % Argument.argument_id
        Argument.argument_id += 1

    def __get__(self, instance, owner):
        if instance is None:
            return self
        elif self.present(instance):
            return getattr(instance, self.arg_id)
        elif callable(self.default):
            return self.default(instance)
        else:
            return self.default

    def present(self, instance):
        return hasattr(instance, self.arg_id)

    def serialize(self, instance, builder=None):
        if hasattr(instance, self.arg_id):
            return getattr(instance, self.arg_id)
        else:
            return self.default

    @abstractmethod
    def __set__(self, instance, value):
        """ Set the property. The value will be a UTF-8 encoded string read from the yaml source file. """


class Boolean(Argument):

    """ Represents a boolean. "1", "yes", "on" and "true" are all considered
    to be True boolean values. Anything else is False. """

    def __set__(self, instance, value):
        if isinstance(value, six.text_type):
            if value.lower() in ("1", "yes", "on", "true"):
                value = True
            else:
                value = False
        else:
            value = bool(value)
        setattr(instance, self.arg_id, value)

    @classmethod
    def _generate_valid(self):
        return random.choice([True, False])


class String(Argument):

    """ Represents a string. """

    def __set__(self, instance, value):
        if value is not None:
            value = force_str(value)
        setattr(instance, self.arg_id, value)

    @classmethod
    def _generate_valid(self):
        glyphs = []
        for i in range(random.randint(0, 1024)):
            glyphs.append(random.choice([
                u"\u2603",
                u"\U0001F42D",
                "/",
                "1",
                "+",
                "-",
                ".",
                "`",
                "\"",
                "'",
                "a",
                "b",
                "c",
                "d",
                "E",
                "F",
            ]))
        return "".join(glyphs)


class FullPath(String):

    """ Represents a full path on the filesystem. This should start with a
    '/'. """

    def __set__(self, instance, value):
        if not value.startswith("/"):
            raise error.ParseError("%s is not a full path" % value)
        super(FullPath, self).__set__(instance, value)

    @classmethod
    def _generate_valid(self):
        return "/" + super(FullPath, self)._generate_valid()


class Integer(Argument):

    """ Represents an integer argument taken from the source file. This can
    throw an :py:exc:error.ParseError if the passed in value cannot represent
    a base-10 integer. """

    def __set__(self, instance, value):
        if not isinstance(value, int):
            try:
                value = int(value)
            except ValueError:
                raise error.ParseError("%s is not an integer" % value)
        setattr(instance, self.arg_id, value)

    @classmethod
    def _generate_valid(self):
        return random.randint(0, sys.maxsize)


class Octal(Integer):

    """ An octal integer.  This is specifically used for file permission modes. """

    def __set__(self, instance, value):
        if not isinstance(value, int):
            value = int(value, 8)
        setattr(instance, self.arg_id, value)


class Dict(Argument):
    def __set__(self, instance, value):
        setattr(instance, self.arg_id, value)

    @classmethod
    def _generate_valid(self):
        return {}


class List(Argument):
    def __set__(self, instance, value):
        setattr(instance, self.arg_id, value)

    @classmethod
    def _generate_valid(self):
        return []


class File(Argument):

    """ Provided with a URL, this can get files by various means. Often used
    with the package:// scheme """

    def __set__(self, instance, value):
        setattr(instance, self.arg_id, value)

    def _generate_valid(self):
        return '/tmp/foo'


class PolicyTrigger:

    def __init__(self, on):
        self.on = on

    def bind(self, resources, target):
        try:
            resource = resources.get_resource_by_name(self.on)
        except:
            try:
                resource = resources[self.on]
            except KeyError:
                raise error.BindingError("Cannot bind %r to missing resource named '%s'" % (target, self.on))

        resource.register_observer('*', target, '*')
        return resource


class SubscriptionArgument(Argument):

    """ Parses the policy: argument for resources, including triggers etc. """

    def __set__(self, instance, value):
        triggers = []
        for resource in value:
            triggers.append(PolicyTrigger(resource))
        setattr(instance, self.arg_id, triggers)

    def serialize(self, instance, builder=None):
        if not hasattr(instance, self.arg_id):
            return
        value = getattr(instance, self.arg_id)
        policy = []
        for t in value:
            policy.append(t.on)
        return policy

    def _generate_valid(self):
        return []


class PolicyArgument(Argument):

    """ Parses the policy: argument for resources, including triggers etc. """

    def __set__(self, instance, value):
        """ Set either a default policy or a set of triggers on the policy collection """
        try:
            setattr(instance, self.arg_id, instance.policies[value](instance))
        except KeyError:
            raise error.ParseError("'%s' is not a valid policy for this %r" % (value, instance))

    def default(self, instance):
        return instance.policies.default()(instance)

    def serialize(self, instance, builder=None):
        if not hasattr(instance, self.arg_id):
            return
        return getattr(instance, self.arg_id).name

    def _generate_valid(self):
        return "invalid-policy"
