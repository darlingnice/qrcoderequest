#!/usr/bin/env python
"""
    descrs.py                        Nat Goodspeed
    Copyright (C) 2022               Nat Goodspeed

Descriptors useful for class customization.

NRG 2022-03-16
"""
from __future__ import absolute_import

import types

class attribute_alias(object):
    """
    This descriptor allows you to designate a given instance attribute as an
    alias for another. Access to either gets you the same object. This is
    useful when you want to update a class's attribute names, without breaking
    legacy consumers.

    class Foo:
        def __init__(self):
            self.bar = [12]
            self.nun = None

        legacy_bar = attribute_alias('bar')

    foo = Foo()
    assert(foo.legacy_bar is foo.bar)
    """
    def __init__(self, attr):
        self.attr = attr

    def __get__(self, obj, cls=None):
        # see https://docs.python.org/3/howto/descriptor.html
        return getattr((cls if obj is None else obj), self.attr)

    def __set__(self, obj, value):
        return setattr(obj, self.attr, value)

    def __delete__(self, obj):
        delattr(obj, self.attr)

class class_or_instance_dispatch(object):
    """
    This descriptor is for when you need a method with a given name to run
    different code depending on whether it is invoked on the class
    (ClassName.method(...)) or on an instance (object.method(...)).

    This can help if you're transitioning an existing method from an attribute
    setter to an alternative constructor. When a legacy caller invokes the
    method on an instance, you must set the attributes on that instance; when
    a new caller invokes the method on the class, you must return a new
    instance of that class.

    You can't distinguish these cases with a normal method definition unless
    you require new callers of the alternative constructor to explicitly pass
    None as the first parameter.

    You can't distinguish these cases by using @classmethod because your
    method is passed the class as first parameter in either case.

    class_or_instance_dispatch isn't a decorator because it takes a pair of
    methods. The classmethod is called if the method name is invoked on the
    class; the instancemethod is called if the method name is invoked on an
    instance.

    class Foo:
        def __init__(self, ab, cd):
            self.attr_setter(ab, cd)

        def attr_setter(self, ab, cd):
            self.ab = ab
            self.cd = cd

        def alt_ctor(cls, ab, cd):
            return cls(ab, cd)

        uniform_method = class_or_instance_dispatch(alt_ctor, attr_setter)

    foo = Foo.uniform_method('ab', 'cd')
    foo.uniform_method('ef', 'gh')
    """
    def __init__(self, classmethod, instancemethod):
        self.classmethod = classmethod
        self.instancemethod = instancemethod

    def __get__(self, obj, cls=None):
        # see https://docs.python.org/3/howto/descriptor.html
        if obj is None:
            return types.MethodType(self.classmethod, cls)
        return types.MethodType(self.instancemethod, obj)

def ownermethod(func):
    """
    In this usage, 'owner' means 'either class or instance'. @ownermethod seems
    less obscure than @eithermethod.

    This allows a mixin class to support operations without having to know
    whether the leaf class's methods are intended to be called on the class or
    on a specific instance.

    class Foo:
        attr = 'class attribute'

        def __init__(self):
            self.attr = 'instance attribute'

        @ownermethod
        def report(owner):
            print(owner.attr)

    Foo.report():   class attribute
    Foo().report(): instance attribute
    """
    # we happen to have the relevant logic already, just with a name that's
    # very unintuitive for this usage
    return class_or_instance_dispatch(func, func)
