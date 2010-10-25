# Copyright 2008 The Tor Project, Inc.  See LICENSE for licensing information.
# Copyright 2010 The Update Framework.  See LICENSE for licensing information.

import re
import sys

import tuf


class Schema:
    """A schema matches a set of possible Python objects, of types
       that are encodable in JSON."""

    def matches(self, obj):
        """Return True if 'obj' matches this schema, False if it doesn't."""
        try:
            self.check_match(obj)
        except tuf.FormatException:
            return False
        else:
            return True

    def check_match(self, obj):
        """Raise thandy.FormatException if 'obj' does not match this schema.
           Abstract method."""
        raise NotImplementedError()


class Any(Schema):
    """
       Matches any single object.

       >>> s = Any()
       >>> s.matches("A String")
       True
       >>> s.matches([1, "list"])
       True
    """

    def check_match(self, obj):
        pass


class RE(Schema):
    """
       Matches any string that matches a given regular expression.

       >>> s = RE("h.*d")
       >>> s.matches("hello world")
       True
       >>> s.matches("Hello World")
       False
       >>> s.matches("hello world!")
       False
       >>> s.matches([33, "Hello"])
       False
    """

    def __init__(self, pat=None, modifiers=0, reObj=None, reName=None):
        """Make a new RE schema
             pat -- The pattern to match, or None if reObj is provided.
             modifiers -- Flags to use when compiling the pattern.
             reObj -- A compiled regular expression object.
        """
        if not reObj:
            if not pat.endswith("$"):
                pat += "$"
            reObj = re.compile(pat, modifiers)
        self._re = reObj
        if reName == None:
            if pat != None:
                reName = "pattern /%s/" % pat
            else:
                reName = "pattern"
        self._reName = reName

    def check_match(self, obj):
        if not isinstance(obj, basestring) or not self._re.match(obj):
            raise tuf.FormatException("%r did not match %s"
                                         % (obj, self._reName))


class Str(Schema):
    """
       Matches a particular string.

       >>> s = Str("Hi")
       >>> s.matches("Hi")
       True
       >>> s.matches("Not hi")
       False
    """

    def __init__(self, val):
        self._str = val

    def check_match(self, obj):
        if self._str != obj:
            raise tuf.FormatException("Expected %r; got %r" % (self._str, obj))


class AnyStr(Schema):
    """
       Matches any string, but no non-string object.

       >>> s = AnyStr()
       >>> s.matches("")
       True
       >>> s.matches("a string")
       True
       >>> s.matches(["a"])
       False
       >>> s.matches(3)
       False
       >>> s.matches(u"a unicode string")
       True
       >>> s.matches({})
       False
    """

    def __init__(self):
        pass

    def check_match(self, obj):
        if not isinstance(obj, basestring):
            raise tuf.FormatException("Expected a string; got %r" % obj)


class OneOf(Schema):
    """
       Matches an object that matches any one of several schemas.

       >>> s = OneOf([ListOf(Int()), Str("Hello"), Str("bye")])
       >>> s.matches(3)
       False
       >>> s.matches("bye")
       True
       >>> s.matches([])
       True
       >>> s.matches([1,2])
       True
       >>> s.matches(["Hi"])
       False
    """

    def __init__(self, alternatives):
        self._subschemas = alternatives

    def check_match(self, obj):
        for m in self._subschemas:
            if m.matches(obj):
                return

        raise tuf.FormatException("Object matched no recognized alternative")


class AllOf(Schema):
    """Matches the intersection of a list of schemas."""

    def __init__(self, required):
        self._subschemas = required[:]

    def check_match(self, obj):
        for s in self._subschemas:
            s.check_match(obj)


class ListOf(Schema):
    """
       Matches a homogenous list of some subschema.

       >>> s = ListOf(RE("(?:..)*"))
       >>> s.matches("hi")
       False
       >>> s.matches([])
       True
       >>> s.matches({})
       False
       >>> s.matches(["Hi", "this", "list", "is", "full", "of", "even", "strs"])
       True
       >>> s.matches(["This", "one", "is not"])
       False

       >>> s = ListOf(Int(), minCount=3, maxCount=10)
       >>> s.matches([3]*2)
       False
       >>> s.matches([3]*3)
       True
       >>> s.matches([3]*10)
       True
       >>> s.matches([3]*11)
       False
    """

    def __init__(self, schema, minCount=0, maxCount=sys.maxint, listName="list"):
        self._schema = schema
        self._minCount = minCount
        self._maxCount = maxCount
        self._listName = listName

    def check_match(self, obj):
        if not isinstance(obj, (list, tuple)):
            raise tuf.FormatException("Expected %s; got %r"
                                         % (self._listName, obj))
        for item in obj:
            try:
                self._schema.check_match(item)
            except tuf.FormatException, e:
                raise tuf.FormatException("%s in %s" % (e, self._listName))

        if not (self._minCount <= len(obj) <= self._maxCount):
            raise tuf.FormatException("Length of %s out of range"
                                         % self._listName)


class Struct(Schema):
    """
       Matches a non-homogenous list of items.

       >>> s = Struct([ListOf(AnyStr()), AnyStr(), Str("X")])
       >>> s.matches(False)
       False
       >>> s.matches("Foo")
       False
       >>> s.matches([[], "Q", "X"])
       True
       >>> s.matches([[], "Q", "D"])
       False
       >>> s.matches([[3], "Q", "X"])
       False
       >>> s.matches([[], "Q", "X", "Y"])
       False

       >>> s = Struct([Str("X")], allowMore=True)
       >>> s.matches([])
       False
       >>> s.matches(["X"])
       True
       >>> s.matches(["X", "Y"])
       True
       >>> s.matches(["X", ["Y", "Z"]])
       True
       >>> s.matches([["X"]])
       False

       >>> s = Struct([Str("X"), Int()], [Int()])
       >>> s.matches([])
       False
       >>> s.matches({})
       False
       >>> s.matches(["X"])
       False
       >>> s.matches(["X", 3])
       True
       >>> s.matches(["X", 3, 9])
       True
       >>> s.matches(["X", 3, 9, 11])
       False
       >>> s.matches(["X", 3, "A"])
       False
    """

    def __init__(self, subschemas, optschemas=[], allowMore=False,
                 structName="list"):
        self._subschemas = subschemas + optschemas
        self._min = len(subschemas)
        self._allowMore = allowMore
        self._structName = structName

    def check_match(self, obj):
        if not isinstance(obj, (list, tuple)):
            raise tuf.FormatException("Expected %s; got %r"
                                         % (self._structName, obj))
        elif len(obj) < self._min:
            raise tuf.FormatException(
                "Too few fields in %s" % self._structName)
        elif len(obj) > len(self._subschemas) and not self._allowMore:
            raise tuf.FormatException(
                "Too many fields in %s" % self._structName)
        for item, schema in zip(obj, self._subschemas):
            schema.check_match(item)


class DictOf(Schema):
    """
       Matches a mapping from items matching a particular key-schema
       to items matching a value-schema.  Note that in JSON, keys must
       be strings.

       >>> s = DictOf(RE(r'[aeiou]+'), Struct([AnyStr(), AnyStr()]))
       >>> s.matches("")
       False
       >>> s.matches({})
       True
       >>> s.matches({"a": ["x", "y"], "e" : ["", ""]})
       True
       >>> s.matches({"a": ["x", 3], "e" : ["", ""]})
       False
       >>> s.matches({"a": ["x", "y"], "e" : ["", ""], "d" : ["a", "b"]})
       False
    """

    def __init__(self, keySchema, valSchema):
        self._keySchema = keySchema
        self._valSchema = valSchema

    def check_match(self, obj):
        try:
            iter = obj.iteritems()
        except AttributeError:
            raise tuf.FormatException("Expected a dict; got %r" % obj)

        for k, v in iter:
            self._keySchema.check_match(k)
            self._valSchema.check_match(v)


class Opt:
    """Helper; applied to a value in Obj to mark it optional.

       >>> s = Obj(k1=Str("X"), k2=Opt(Str("Y")))
       >>> s.matches({'k1': "X", 'k2': "Y"})
       True
       >>> s.matches({'k1': "X", 'k2': "Z"})
       False
       >>> s.matches({'k1': "X"})
       True
    """

    def __init__(self, schema):
        self._schema = schema

    def check_match(self, obj):
        self._schema.check_match(obj)


class Obj(Schema):
    """
       Matches a dict from specified keys to key-specific types.  Unrecognized
       keys are allowed.

       >>> s = Obj(a=AnyStr(), bc=Struct([Int(), Int()]))
       >>> s.matches({'a':"ZYYY", 'bc':[5,9]})
       True
       >>> s.matches({'a':"ZYYY", 'bc':[5,9], 'xx':5})
       True
       >>> s.matches({'a':"ZYYY", 'bc':[5,9,3]})
       False
       >>> s.matches({'a':"ZYYY"})
       False
    """

    def __init__(self, _objname="object", **d):
        self._objname = _objname
        self._required = d.items()

    def check_match(self, obj):
        if not isinstance(obj, dict):
            raise tuf.FormatException("Wanted a %s; did not get a dict" %
                                         self._objname)

        for k, schema in self._required:
            try:
                item = obj[k]
            except KeyError:
                if not isinstance(schema, Opt):
                    raise tuf.FormatException("Missing key %s in %s"
                                                 % (k, self._objname))

            else:
                try:
                    schema.check_match(item)
                except tuf.FormatException, e:
                    raise tuf.FormatException("%s in %s.%s"
                                                 % (e, self._objname, k))


class TaggedObj(Schema):
    """
       Matches an object based on the value of a particular 'tag' field.
       If tagIsOptional, matches any object when the tag is missing.
       If ignoreUnrecognized, matches any object when the tag is present
       but the value is not one we know.

       >>> s = TaggedObj('tp', a=Obj(int1=Int()), b=Obj(s=AnyStr()))
       >>> s.matches(3)
       False
       >>> s.matches([])
       False
       >>> s.matches({})
       False
       >>> s.matches({'tp' : 'fred'})
       True
       >>> s.matches({'tp' : 'a'})
       False
       >>> s.matches({'tp' : 'a', 'int1': 3})
       True
       >>> s.matches({'tp' : 'a', 'int1': []})
       False
       >>> s.matches({'tp' : 'b', 'int1': 3, 's': 'tt'})
       True
    """

    def __init__(self, tagName, tagIsOptional=False, ignoreUnrecognized=True,
                 **tagvals):
        self._tagName = tagName
        self._tagOpt = tagIsOptional
        self._ignoreOthers = ignoreUnrecognized
        self._tagvals = tagvals

    def check_match(self, obj):
        try:
            tag = obj[self._tagName]
        except KeyError:
            if self._tagOpt:
                return
            else:
                raise tuf.FormatException("Missing tag %s on object" %
                                             self._tagName)
        except TypeError:
            raise tuf.FormatException("Got a %s, not a tagged object" %
                                         type(obj))
        if not isinstance(tag, basestring):
            raise tuf.FormatException("Expected a string for %s; got a %s" % (
                    self._tagName, type(tag)))
        try:
            subschema = self._tagvals[tag]
        except KeyError:
            if self._ignoreOthers:
                return
            else:
                raise tuf.FormatException("Unrecognized value %s for %s" % (
                        tag, self._tagName))

        subschema.check_match(obj)


class Int(Schema):
    """
       Matches an integer.

       >>> s = Int()
       >>> s.matches(99)
       True
       >>> s.matches(False)
       False
       >>> s.matches(0L)
       True
       >>> s.matches("a string")
       False
       >>> Int(lo=10, hi=30).matches(25)
       True
       >>> Int(lo=10, hi=30).matches(5)
       False
    """

    def __init__(self, lo= -sys.maxint, hi=sys.maxint):
        self._lo = lo
        self._hi = hi

    def check_match(self, obj):
        if isinstance(obj, bool) or not isinstance(obj, (int, long)):
            # We need to check for bool as a special case, since bool
            # is for historical reasons a subtype of int.
            raise tuf.FormatException("Got %r instead of an integer" % obj)
        elif not (self._lo <= obj <= self._hi):
            raise tuf.FormatException("%r not in range [%r,%r]"
                                         % (obj, self._lo, self._hi))


class Bool(Schema):
    """
       Matches a boolean.

       >>> s = Bool()
       >>> s.matches(True) and s.matches(False)
       True
       >>> s.matches(11)
       False
    """

    def __init__(self):
        pass

    def check_match(self, obj):
        if not isinstance(obj, bool):
            raise tuf.FormatException("Got %r instead of a boolean" % obj)


class Func(Schema):

    def __init__(self, fn, baseSchema=None):
        self._fn = fn
        self._base = baseSchema

    def check_match(self, obj):
        if self._base:
            self._base.check_match(obj)
        r = self._fn(obj)
        if r is False:
            raise tuf.FormatException("%s returned False" % self._fn)
