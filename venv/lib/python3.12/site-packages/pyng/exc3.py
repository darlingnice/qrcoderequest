#!/usr/bin/env python3
"""\
@file   exc3.py
@author Nat Goodspeed
@date   2022-01-31
@brief  

$LicenseInfo:firstyear=2022&license=internal$
Copyright (c) 2022, Linden Research, Inc.
$/LicenseInfo$
"""

import contextlib

# ****************************************************************************
#   suppress_but_log
# ****************************************************************************
class suppress_but_log(contextlib.ContextDecorator):
    """
    Like contextlib.suppress(), but logs any exception of one of the specified
    exception types that occurs. suppress_but_log produces a single log line,
    rather than a whole traceback.

    suppress_but_log can be used either as a context manager:

    with suppress_but_log(log, "description", SomeExceptionType):
        # ... code that might raise SomeExceptionType ...

    or as a decorator:

    @suppress_but_log(log, "description", SomeExceptionTypes...)
    def func(...):
        # ... function body that might raise SomeExceptionTypes ...

    Its use as a decorator also permits (e.g.):

    cleanup = contextlib.ExitStack()
    cleanup.callback(suppress_but_log(log, "description", SomeExceptionType)(actual_func))
    """
    def __init__(self, log, description, *exceptions):
        """
        log: the logger on which to report any exception
        exceptions: arbitrary exception classes any exception for which
        isinstance(exception, exceptions) will be caught and logged; any other
        exception will propagate. If you pass no exceptions, any Exception
        will be caught.
        """
        self.log = log
        self.description = description
        self.exceptions = exceptions or (Exception,)

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        if value:
            self.log.warning('*** Error trying to %s: %s: %s',
                             self.description, value.__class__.__name__, value)
            return isinstance(value, self.exceptions)

# ****************************************************************************
#   LoggingExitStack
# ****************************************************************************
class LoggingExitStack(contextlib.ExitStack):
    """
    Like contextlib.ExitStack(), with a callback() method that implicitly
    wraps the passed callable with suppress_but_log.

    If a callable passed to ExitStack.callback() raises an exception,
    ExitStack processing continues, but the exception is saved and re-raised
    on completion. LoggingExitStack is for use when we want to
    suppress_but_log any specified exception raised by any callback()
    callable.
    """
    def __init__(self, *args, **kwds):
        # ExitStack needs no constructor parameters
        super().__init__()
        self.suppressor = suppress_but_log(*args, **kwds)

    def callback(self, callback, /, *args, **kwds):
        super().callback(self.suppressor(callback), *args, **kwds)
