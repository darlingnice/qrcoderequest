#!/usr/bin/env python3
"""\
@file   throttled_proxy.py
@author Nat Goodspeed
@date   2023-05-16
@brief  ThrottledProxy class
"""

from __future__ import absolute_import
import functools
from .pickles import WrappingProxy, WrappingProxyFamily
import time

try:
    # monotonic() was introduced in Python 3.3
    monotonic = time.monotonic
except AttributeError:
    # not there yet, fall back to plain time.time()
    monotonic = time.time

try:
    from eventlet import sleep
    from eventlet.semaphore import Semaphore
except ImportError as err:
    import logging
    logging.warning("Can't import eventlet, working around: %s", err)
    # sleep() is easy enough
    from time import sleep
    # Semaphore is a context manager that ThrottledRESTService instantiates
    # once and then reuses multiple times, so we can't fake it with a
    # @contextmanager function. And until we can rely on Python 3.7+
    # everywhere, even if we try for contextlib.nullcontext, we'd still need
    # to write out the whole fallback below -- so just use the fallback.
    class Semaphore(object):
        def __init__(*args, **kwds):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            # don't swallow exceptions
            return False


class Throttle(object):
    """
    Throttle is a Context Manager that rate-limits any entry to a 'with'
    statement body. Usage:

    # store this somewhere it will be reused by every access to the target
    # resource
    throttle = Throttle(1.0)
    with throttle:
        # this body, or any other 'with' statement referencing the same
        # Throttle instance, will be entered no more than once per second
        # ...
    """
    def __init__(self, interval):
        """
        interval: minimum time in seconds between successive entry to any
                  'with' statement referencing this Throttle instance
        """
        self.interval = interval

        # Let's say we have just entered at time (t-0.1), so the next time it
        # should be safe to enter again will be at (t-0.1+__interval), let's
        # say 0.6. But now, at time t, because our greenthreads tend to be
        # somewhat bursty, several greenthreads more or less simultaneously
        # call our __enter__() method. The first one reaches the code below
        # and realizes it must sleep(0.6). Context switches to the next
        # greenthread, which reaches the code below and realizes it must
        # sleep(0.5). Context switches to the next, which realizes it must
        # sleep(0.4)... All wake at more or less the same time and pass into
        # the 'with' body, exceeding the rate limit.

        # So we must serialize access to the delay logic. Use a Semaphore.
        self.throttle = Semaphore(1)

        # We haven't yet entered even once. First entry needs no delay!
        self.nexttime = 0

    def __enter__(self):
        # serialize the whole body of our 'with' statement with our Semaphore
        self.throttle.__enter__()
        # how long until it's safe to make the next call?
        delay = self.nexttime - monotonic()
        # if it's still in the future, wait that long
        if delay > 0:
            sleep(delay)
        # About to enter block: it won't be safe to enter again until
        # (now + interval), bearing in mind that (due to the sleep() call
        # above) 'now' could be different than on entry.
        self.nexttime = monotonic() + self.interval

    def __exit__(self, *args):
        # release the Semaphore
        self.throttle.__exit__(*args)
        # don't swallow exceptions
        return False

    def wrap(self, func):
        """
        Wrap a function such that any call to the resulting function is a
        rate-limited call to the original function.

        n.b. Given a Throttle instance 'throttle', @throttle.wrap can be used
        as a decorator.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwds):
            # rate-limit any call to func with this Throttle instance
            with self:
                return func(*args, **kwds)
        return wrapper


class ThrottledProxy(WrappingProxy):
    """
    ThrottledProxy is a proxy class that rate-limits calls to (specified
    methods of) the target object. This is useful for talking to a remote
    service with rate limits.

    It is especially useful when multiple eventlet greenthreads might be
    trying to talk to the same remote service. Of course you must arrange for
    them all to use the same Throttle.
    """
    def __init__(self, target, throttle, limit=(), nolimit=(), limiter=None):
        """
        target:   the object whose request rate we must control
        throttle: a Throttle instance embedding the actual interval
        limit:    iterable of method names subject to rate limiting; all others
                  are unlimited
        nolimit:  iterable of method names to be left unlimited; all others are
                  rate-limited
        limiter:  callable(method name) that returns True if the method with
                  that name should be rate-limited

        Passing more than one of 'limit', 'nolimit' and 'limiter' raises
        TypeError. If none are specified, all methods are rate-limited.
        """
        super(ThrottledProxy, self).__init__(
            target,
            wrapper=throttle.wrap,
            wrap=limit,
            nowrap=nolimit,
            should_wrap=limiter)


class ThrottledProxyFamily(WrappingProxyFamily):
    """
    Use ThrottledProxyFamily to wrap a class whose methods can deliver
    instances of other classes that must themselves be throttled with the same
    Throttle.
    """
    def __init__(self, target, throttle, limit=(), nolimit=(), limiter=None,
                 alsowrap=()):
        """
        target:   the object whose request rate we must control
        throttle: a Throttle instance embedding the actual interval
        limit:    iterable of method names subject to rate limiting; all others
                  are unlimited
        nolimit:  iterable of method names to be left unlimited; all others are
                  rate-limited
        limiter:  callable(method name) that returns True if the method with
                  that name should be rate-limited
        alsowrap: a class or a tuple of classes: any instance of these classes
                  returned by any wrapped method will itself be wrapped in a
                  ThrottledProxyFamily instance with the same Throttle

        Passing more than one of 'limit', 'nolimit' and 'limiter' raises
        TypeError. If none are specified, all methods are rate-limited.
        """
        super(ThrottledProxyFamily, self).__init__(
            target,
            wrapper=throttle.wrap,
            wrap=limit,
            nowrap=nolimit,
            should_wrap=limiter,
            alsowrap=alsowrap)
