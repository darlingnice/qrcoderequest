#!/usr/bin/python
"""\
@file   pickles.py
@author Nat Goodspeed
@date   2020-04-28
@brief  Utilities helpful for [un]pickling
"""

import functools

class PickleableProxy(object):
    """
    Evidently unpickling tests for some method by trying to access it and
    catching AttributeError. But since unpickling creates an empty object with
    no data attributes, bypassing the constructor, when pickle tries to access
    that method, our proxy-object __getattr__() would try to access
    self._target, which is *not yet defined*, so recursively calls
    __getattr__() again... Before introducing this class, we were blowing up
    with infinite recursion on unpickling.

    This class by itself, initialized with (a reference to) some other object,
    should behave pretty much exactly like that other object. The point is to
    derive a subclass, whose methods will intercept any calls to the
    corresponding methods on the target object. Your subclass override method
    can forward calls to the original target object by calling
    self._target.method().
    """
    # Define the initial _target as a class attribute so that, on unpickling,
    # getattr() will find the class attribute even before the instance
    # attribute is reloaded. Therefore self._target.whatever will raise
    # AttributeError instead of recursively calling __getattr__().
    _target = None

    def __init__(self, target):
        self._target = target

    def __getattr__(self, attr):
        """
        When our consumer references any attribute not specifically
        overridden, return the corresponding one from our target object.
        """
        return getattr(self._target, attr)


class WrappingProxy(PickleableProxy):
    """
    WrappingProxy is a proxy class that wraps calls to (specified methods of)
    the target object using a specified wrapper function. The function must
    accept the original target method and return one wrapped as desired.
    WrappingProxy caches the result so that the wrapper will only be called
    the first time a given method is referenced.
    """
    def __init__(self, target, wrapper, wrap=(), nowrap=(), should_wrap=None):
        """
        target:      the object whose methods we should wrap
        wrapper:     a callable accepting target method, returning wrapped
                     method
        wrap:        iterable of method names that should be wrapped; all
                     others are left unwrapped
        nowrap:      iterable of method names to be left unwrapped; all others
                     are wrapped
        should_wrap: callable(method name) that returns True if the method with
                     that name should be wrapped

        Passing more than one of 'wrap', 'nowrap' and 'should_wrap' raises
        TypeError. If none are specified, all methods are wrapped.

        The callable returned by wrapper() will be passed through
        functools.wraps() to pick up the target method's name et al.
        """
        # pass target to PickleableProxy
        super(WrappingProxy, self).__init__(target)
        self.__wrapper = wrapper

        wparams = [w for w in (wrap, nowrap, should_wrap) if w]
        if len(wparams) > 1:
            raise TypeError('Pass WrappingProxy.__init__() '
                            'at most one of wrap, nowrap or should_wrap')
        if not wparams:
            self._test = lambda method: True
        elif wrap:
            wrap = set(wrap)
            self._test = lambda method: method in wrap
        elif nowrap:
            nowrap = set(nowrap)
            self._test = lambda method: method not in nowrap
        else: # should_wrap
            self._test = should_wrap

    def __getattr__(self, attr):
        """
        The first time any callable attribute is referenced, if it should be
        wrapped, cache and return a wrapped method.

        If the referenced method shouldn't be wrapped, cache and return the
        unwrapped method.

        If the referenced attribute isn't callable, directly return the target
        object's attribute.
        """
        attribute = getattr(self._target, attr)
        if not callable(attribute):
            # caller wants the live attribute on the target object
            return attribute

        # attribute is a method
        if not self._test(attr):
            # this method shouldn't be wrapped
            setattr(self, attr, attribute)
            return attribute

        # Because we cache our wrapper method for future reference, we only
        # reach this __getattr__() method the first time a given attribute is
        # referenced.
        wrapped = functools.wraps(attribute)(self.__wrapper(attribute))
        setattr(self, attr, wrapped)
        return wrapped


class WrappingProxyFamily(WrappingProxy):
    """
    Use WrappingProxyFamily to wrap a class whose methods might deliver
    instances of other classes that must themselves be wrapped with the same
    wrapper.
    """
    def __init__(self, target, wrapper, *args, alsowrap=(), **kwds):
        """
        target:      the object whose methods we should wrap
        wrapper:     a callable accepting target method, returning wrapped
                     method
        wrap:        iterable of method names that should be wrapped; all
                     others are left unwrapped
        nowrap:      iterable of method names to be left unwrapped; all others
                     are wrapped
        should_wrap: callable(method name) that returns True if the method with
                     that name should be wrapped
        alsowrap:    a class or a tuple of classes: any instance of these
                     classes returned by any wrapped method will itself be
                     wrapped in a WrappingProxyFamily instance with the same
                     wrapper
        """
        self.__alsowrap = alsowrap

        def meta_wrapper(method):
            # wrap method with caller's wrapper (bound by inline def)
            wrapped = wrapper(method)

            def propagate(*args, **kwds):
                # call the wrapped method
                value = wrapped(*args, **kwds)
                if not isinstance(value, self.__alsowrap):
                    # not an alsowrap object, just return
                    return value

                # aha, wrapped method returned an alsowrap object: wrap it
                return WrappingProxyFamily(
                    value, wrapper=wrapper,
                    should_wrap=self._test,
                    alsowrap=self.__alsowrap)

            # meta_wrapper() returns the propagate() wrapper
            return propagate

        # now use meta_wrapper() as the wrapper for WrappingProxy base class
        super(WrappingProxyFamily, self).__init__(
            target, wrapper=meta_wrapper, *args, **kwds)
