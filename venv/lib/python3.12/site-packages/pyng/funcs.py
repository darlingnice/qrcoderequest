#!/usr/bin/python
"""
    funcs.py                         Nat Goodspeed
    Copyright (C) 2024               Nat Goodspeed

NRG 2024-01-05
"""

class compose:
    """
    compose(f, g, h) returns a function C such that C(*args, **kwds) returns
    f(g(h(*args, **kwds))).

    This is very like the compose() function found in Django tests, though it
    was developed independently:
    https://github.com/django/django/blob/main/tests/decorators/tests.py#L34-L44

    If maketup() returns an iterable, and we want to pass each item in the
    iterable as a positional argument to posargs():

    compose(pcall(posargs), maketup)

    If maketup() returns a tuple longer than the number of posarg()'s
    positional parameters:

    compose(pcall(posargs), operator.itemgetter(slice(0,3)), maketup)

    If makedict() returns a dict, and we want to pass each item in the dict as
    a keyword argument to keyargs():

    compose(kcall(keyargs), makedict)
    """
    def __init__(self, *funcs):
        self.rfuncs = list(reversed(funcs))

    def __call__(self, *args, **kwds):
        if self.rfuncs:
            # Here rfuncs is not empty.
            # Call the first/innermost one with (*args, **kwds).
            result = self.rfuncs[0](*args, **kwds)
            # Pass that result as the sole positional argument to each successive
            # outer function. If you want to interpret it as positional arguments,
            # wrap the function in pcall(). If you want to interpret it as keyword
            # arguments, wrap the function in kcall().
            for func in self.rfuncs[1:]:
                result = func(result)
            return result

        # Funny case of plain nullary compose(). We could say that compose()
        # is an error, save that it's kind of compelling to make compose()
        # return the identity function, whether the argument is passed as
        # positional or keyword. Following that line of reasoning, we could
        # make it a strictly unary identity function (else error), or we could
        # make it pass through its arguments in some form. We choose the
        # latter.
        if not kwds:
            if len(args) == 1:
                # compose()(x) => x
                return args[0]
            else:
                # compose()() => (), compose()(x, y) => (x, y)
                return args
        elif not args:
            if len(kwds) == 1:
                # compose()(only=x) => x
                return next(iter(kwds.values()))
            else:
                # compose()(first=x, second=y) => {'first': x, 'second': y}
                return kwds
        else:
            # compose()(x, y, ..., k0=a, k1=b, ...) =>
            # ((x, y, ...), {'k0': a, 'k1': b, ...})
            # In other words, if you pass a nullary compose() result both
            # positional args and keyword args, you get back a tuple
            # containing the positional args tuple and the keyword args
            # dict. In that funny case we don't special-case either being
            # a single item.
            return (args, kwds)


class pcall:
    """
    pcall(func) returns a function F such that F((a, b, c, ...)) returns
    func(a, b, c, ...)

    In other words, pcall() wraps the passed function to accept any iterable
    and expand that iterable to individual function positional arguments.
    """
    def __init__(self, func):
        self.func = func

    def __call__(self, args):
        return self.func(*args)


class kcall:
    """
    kcall(func) returns a function F such that
    F({'k1': a, 'k2': b, 'k3': c, ...}) returns func(k1=a, k2=b, k3=c, ...)

    In other words, kcall() wraps the passed function to accept any dict
    and expand that dict to individual function keyword arguments.
    """
    def __init__(self, func):
        self.func = func

    def __call__(self, kwds):
        return self.func(**kwds)


class pkcall:
    """
    pkcall(func) returns a function F such that
    F(((x, y, z, ...), {'k1': a, 'k2': b, 'k3': c, ...})) returns
    func(x, y, z, ..., k1=a, k2=b, k3=c, ...)

    In other words, pcall() wraps the passed function to accept a tuple of
    (iterable, dict)
    and expand the iterable to positional arguments and the dict to keyword
    arguments for the wrapped function.
    """
    def __init__(self, func):
        self.func = func

    def __call__(self, args_kwds):
        return self.func(*args_kwds[0], **args_kwds[1])
