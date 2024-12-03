#!/usr/bin/python
"""\
@file   logs.py
@author Nat Goodspeed
@date   2022-02-03
@brief  Utilities for working with Python logging

Copyright (c) 2022, Nat Goodspeed
"""

import functools
import itertools
import logging
from pyng.exc import describe

# define EXCEPTION as an entity distinct from any possible future log level
# value in the logging module
EXCEPTION = object()

# ****************************************************************************
#   log_calls
# ****************************************************************************
def log_calls(logger=None, level=logging.DEBUG, exclevel=logging.DEBUG):
    """
    This decorator interposes a wrapper that logs entry and exit to the
    decorated 'func', with its parameters and return value (or exception).

    Usage:

    @log_calls
    def somefunc(...args...):
        # ...

    Each call to somefunc() will be logged to a logger named
    "module.somefunc". This is deemed to be a plausible default logger.
    Positional and keyword arguments are logged as such. If somefunc() returns
    normally, its return value will be logged; if it raises an exception, the
    exception will be logged. Logging is at level logging.DEBUG by default: it
    is assumed that showing calls and returns from an individual function is
    of interest to the developer, rather than a production user.

    @log_calls()
    def somefunc(...args...):
        # ...

    Same, except messages are logged to the root logger. Passing parameters to
    the log_calls decorator implies you want to control the logger and/or the
    log level, and getLogger(None) retrieves the root logger.

    @log_calls(logger=None, level=logging.DEBUG, exclevel=logging.DEBUG)
    def somefunc(...args...):
        # ...

    This form logs calls to a specific logger. If 'logger' is a logging.Logger
    instance, that will be used, else it is passed to logging.getLogger().
    'level' controls the log level of call and normal return messages.
    'exclevel' controls the log level of exception messages. If you pass
    exclevel=logs.EXCEPTION, that's recognized as a special case: the
    exception is logged with logging.Logger.exception(), which adds exception
    information to the log message.
    """
    # First check for the funny @log_calls case, that is, the case of no
    # parameters: when the function name is used as the decorator. Python
    # passes the decorated function as 'logger'.
    if callable(logger):
        # logging.Logger instances aren't callable()
        func = logger
        # Use the documented default logger for this case.
        deco = _log_calls(logger='.'.join((func.__module__, func.__name__)),
                          level=level,
                          exclevel=exclevel)
        # In this case, Python has already called the decorator (this function
        # name) passing the decorated function, so actually apply the decorator.
        return deco(func)

    # When passed explicit arguments, this function is just an alias for
    # _log_calls. This call is to *obtain* the decorator, not yet to *apply*
    # it. Just return the decorator object.
    return _log_calls(logger=logger, level=level, exclevel=exclevel)

class _log_calls(object):
    def __init__(self, logger, level, exclevel):
        # Make sure that if we're passed an existing logger, we simply use
        # that one.
        self.logger   = (logger if isinstance(logger, logging.Logger)
                         else logging.getLogger(logger))
        self.level    = level
        self.exclevel = exclevel

    def __call__(self, func):
        # Resolve log functions for normal calls and exception logging before
        # binding them into the wrapper, rather than deciding on every call.
        log = functools.partial(self.logger.log, self.level)
        exclog = (self.logger.exception if self.exclevel is EXCEPTION
                  else functools.partial(self.logger.log, self.exclevel))
        @functools.wraps(func)
        def wrapper(*args, **kwds):
            name = func.__name__
            log("{}({})".format(name,
                                ", ".join(itertools.chain((repr(arg) for arg in args),
                                                          ("{}={!r}".format(*item)
                                                           for item in kwds.items())))))
            try:
                result = func(*args, **kwds)
            except Exception as err:
                exclog("{}() raised {}".format(name, describe(err)))
                raise
            else:
                log("%s() => %r", name, result)
                return result

        return wrapper
