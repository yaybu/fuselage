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
import unicodedata
import random

from fuselage import error


class Argument(object):

    """ Stores the argument value on the instance object. It's a bit fugly,
    neater ways of doing this that do not involve passing extra arguments to
    Argument are welcome. """

    metaclass = ABCMeta
    argument_id = 0

    def __init__(self, **kwargs):
        self.default = kwargs.pop("default", None)
        self.__doc__ = kwargs.pop("help", None)
        self.arg_id = "argument_%d" % Argument.argument_id
        Argument.argument_id += 1

    def __get__(self, instance, owner):
        if instance is None:
            # sphinx complains?
            #raise AttributeError
            return None
        if hasattr(instance, self.arg_id):
            return getattr(instance, self.arg_id)
        else:
            return self.default

    def serialize(self, instance):
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
        if isinstance(value, six.string_types):
            if value.lower() in ("1", "yes", "on", "true"):
                value = True
            else:
                value = False
        else:
            value = bool(value)
        setattr(instance, self.arg_id, value)


class String(Argument):

    """ Represents a string. """

    try:
        UNICODE_TYPE = unicode
    except NameError:
        UNICODE_TYPE = str

    def __set__(self, instance, value):
        if value is None:
            pass
        elif not isinstance(value, (self.UNICODE_TYPE,)):
            value = self.UNICODE_TYPE(value, 'utf-8')
        setattr(instance, self.arg_id, value)

    @classmethod
    def _get_unicode_glyphs(self):
        return ''.join(
            unichr(char)
            for char in range(sys.maxunicode + 1)
            if unicodedata.category(unichr(char))[0] in ('LMNPSZ')
        )

    @classmethod
    def _generate_valid(self):
        unicode_glyphs = self._get_unicode_glyphs()
        l = []
        for i in range(random.randint(0, 1024)):
            l.append(random.choice(unicode_glyphs))
        return "".join(l)


class FullPath(String):

    """ Represents a full path on the filesystem. This should start with a
    '/'. """

    def __set__(self, instance, value):
        if not value.startswith("/"):
            raise error.ParseError("%s is not a full path" % value)
        super(FullPath, self).__set__(instance, value)

    @classmethod
    def _generate_valid(self):
        # TODO: needs work
        unicode_glyphs = self._get_unicode_glyphs()
        l = []
        for i in range(random.randint(0, 1024)):
            l.append(random.choice(unicode_glyphs))
        return "/" + "".join(l)


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
        return random.randint(0, sys.maxint)


class Octal(Integer):

    """ An octal integer.  This is specifically used for file permission modes. """

    def __set__(self, instance, value):
        if isinstance(value, int):
            # we assume this is due to lame magic in yaml and rebase it
            value = int(str(value), 8)
        else:
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


class StandardPolicy:

    def __init__(self, policy_name):
        self.policy_name = policy_name


class PolicyTrigger:

    def __init__(self, policy, when, on):
        self.policy = policy
        self.when = when
        self.on = on

    def bind(self, resources, target):
        if self.on in resources:
            resources[self.on].register_observer(self.when, target, self.policy)
        else:
            raise error.BindingError("Cannot bind %r to missing resource named '%s'" % (target, self.on))
        return resources[self.on]


class PolicyCollection:

    """ A collection of policy structures. """

    literal = None
    """ The policy that is set as the "standard" policy, not one that depends on a trigger. """

    triggers = ()
    """ A list of PolicyTrigger objects that represent optional triggered policies. """

    def __init__(self, literal=None, triggers=()):
        self.literal = literal
        self.triggers = triggers

    def literal_policy(self, resource):
        if self.literal is not None:
            return resource.policies[self.literal.policy_name]
        else:
            import policy
            return policy.NullPolicy

    def all_potential_policies(self, resource):
        if self.literal:
            yield resource.policies[self.literal.policy_name]
        else:
            for pol in set(t.policy for t in self.triggers):
                yield resource.policies[pol]


class PolicyArgument(Argument):

    """ Parses the policy: argument for resources, including triggers etc. """

    def __set__(self, instance, value):
        """ Set either a default policy or a set of triggers on the policy collection """
        if isinstance(value, six.string_types):
            coll = PolicyCollection(StandardPolicy(value))
        else:
            triggers = []
            for policy, conditions in value.items():
                if not isinstance(conditions, list):
                    conditions = [conditions]
                for condition in conditions:
                    triggers.append(
                        PolicyTrigger(
                            policy=policy,
                            when=condition['when'],
                            on=condition['on'],
                        )
                    )
            coll = PolicyCollection(triggers=triggers)
        setattr(instance, self.arg_id, coll)
