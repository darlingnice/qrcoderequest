#!/usr/bin/python
"""\
@file   file_arg.py
@author Nat Goodspeed
@date   2020-02-13
@brief  Utilities for accepting command-line arguments to specify files

Copyright (c) 2020, Nat Goodspeed
"""

from argparse import ArgumentParser
import glob
import itertools
import os
from pathlib import Path

# Never traverse down into these directories.
IGNORE_DIRS = ('CVS', '.svn', '.hg', '.git', '__pycache__')

# ****************************************************************************
#   The mumble_arg() functions that follow are for use as parents=[] in an
#   argparse.ArgumentParser for a script that lets the user specify multiple
#   files.
#   * file_arg() lets the user specify individual files (or wildcards)
#   * dir_arg()  lets the user include the files in each specified directory
#   * file_or_dir_arg() lets the user specify either individual files or,
#     for each directory, imply all top-level files therein
#   * tree_arg() lets the user recursively include the files in the whole
#     directory tree under each specified directory
#   * file_or_tree_arg() lets the user specify either individual files or,
#     for each directory, imply all files at any depth under that tree
# ****************************************************************************
def file_arg(*args, **kwds):
    """
    Return an ArgumentParser that defines a file argument, suitable for
    passing as one of the parents= of the real ArgumentParser.

    Pass the switches you want to use, e.g. file_arg('-f', '--file'). Or, if
    you want to collect positional arguments, e.g. file_arg('files'). Note
    that for positional arguments, argparse uses the argument name as 'dest'.

    If you intend to use this argument with an ArgumentParser with non-
    default prefix_chars, you must pass the same prefix_chars to file_arg().

    Pass any argparse.ArgumentParser.add_argument() arguments you want, but
    file_arg() provides defaults:

    dest:    'files'
    nargs:   for a switch, '+'; for a positional argument, '*'
    default: []
    metavar: 'FILE'
    help:    'consider each {metavar} specified'

    The default 'dest' can be useful with files_from().
    """
    return _arg(args, kwds,
                dest='files',
                metavar='FILE',
                help='consider each {metavar} specified')

def dir_arg(*args, **kwds):
    """
    Return an ArgumentParser that defines a dir argument, suitable for
    passing as one of the parents= of the real ArgumentParser.

    Pass the switches you want to use, e.g. dir_arg('-d', '--dir'). Or, if
    you want to collect positional arguments, e.g. dir_arg('dirs'). Note
    that for positional arguments, argparse uses the argument name as 'dest'.

    If you intend to use this argument with an ArgumentParser with non-
    default prefix_chars, you must pass the same prefix_chars to dir_arg().

    Pass any argparse.ArgumentParser.add_argument() arguments you want, but
    dir_arg() provides defaults:

    dest:    'dirs'
    nargs:   for a switch, '+'; for a positional argument, '*'
    default: []
    metavar: 'DIR'
    help:    'consider all files at top level of each {metavar}'

    The default 'dest' can be useful with files_from().
    """
    return _arg(args, kwds,
                dest='dirs',
                metavar='DIR',
                help='consider all the files at top level of each {metavar}')

def file_or_dir_arg(*args, **kwds):
    """
    Return an ArgumentParser that defines a file/dir argument, suitable for
    passing as one of the parents= of the real ArgumentParser.

    Pass the switches you want to use, e.g. file_or_dir_arg('--dir').
    Or, if you want to collect positional arguments, e.g.
    file_or_dir_arg('files_or_dirs'). Note that for positional arguments,
    argparse uses the argument name as 'dest'.

    If you intend to use this argument with an ArgumentParser with non-
    default prefix_chars, you must pass the same prefix_chars to
    file_or_dir_arg().

    Pass any argparse.ArgumentParser.add_argument() arguments you want, but
    file_or_dir_arg() provides defaults:

    dest:    'files_or_dirs'
    nargs:   for a switch, '+'; for a positional argument, '*'
    default: []
    metavar: 'FILE or DIR'
    help:    'consider each FILE specified, plus
              all files at top level of each DIR'

    The default 'dest' can be useful with files_from().
    """
    return _arg(args, kwds,
                dest='files_or_dirs',
                metavar='FILE or DIR',
                help='consider each FILE specified, plus '
                     'all the files at top level of each DIR')

def tree_arg(*args, **kwds):
    """
    Return an ArgumentParser that defines a directory tree argument, suitable
    for passing as one of the parents= of the real ArgumentParser.

    Pass the switches you want to use, e.g. tree_arg('-t', '--tree'). Or, if
    you want to collect positional arguments, e.g. tree_arg('trees'). Note
    that for positional arguments, argparse uses the argument name as 'dest'.

    If you intend to use this argument with an ArgumentParser with non-
    default prefix_chars, you must pass the same prefix_chars to tree_arg().

    Pass any argparse.ArgumentParser.add_argument() arguments you want, but
    tree_arg() provides defaults:

    dest:    'trees'
    nargs:   for a switch, '+'; for a positional argument, '*'
    default: []
    metavar: 'BASEDIR'
    help:    'recursively consider all files in each {metavar} tree'

    The default 'dest' can be useful with files_from().
    """
    return _arg(args, kwds,
                dest='trees',
                metavar='BASEDIR',
                help='recursively walk all the files in each {metavar}')

def file_or_tree_arg(*args, **kwds):
    """
    Return an ArgumentParser that defines a file or directory tree argument,
    suitable for passing as one of the parents= of the real ArgumentParser.

    Pass the switches you want to use, e.g. file_or_tree_arg('-t', '--tree').
    Or, if you want to collect positional arguments, e.g.
    file_or_tree_arg('files_or_trees'). Note that for positional arguments,
    argparse uses the argument name as 'dest'.

    If you intend to use this argument with an ArgumentParser with non-
    default prefix_chars, you must pass the same prefix_chars to
    file_or_tree_arg().

    Pass any argparse.ArgumentParser.add_argument() arguments you want, but
    file_or_tree_arg() provides defaults:

    dest:    'files_or_trees'
    nargs:   for a switch, '+'; for a positional argument, '*'
    default: []
    metavar: 'FILE or BASEDIR'
    help:    'consider each FILE specified, plus
              all files at any depth under each BASEDIR tree'

    The default 'dest' can be useful with files_from().
    """
    return _arg(args, kwds,
                dest='files_or_trees',
                metavar='FILE or BASEDIR',
                help='consider each FILE specified, plus '
                     'all the files at any depth under each BASEDIR tree')

def _arg(args, kwds, dest, metavar, help, default=[]):
    """
    args:    from caller's *args
    kwds:    from caller's **kwds
    dest:    default 'dest' if not overridden in kwds
    metavar: default 'metavar' if not overridden in kwds
    help:    default 'help' if not overridden in kwds
    default: default 'default' if not overridden in kwds
    """
    # extract our prefix_chars argument: this is NOT supported by (or passed
    # to) add_argument(); we need it so we can spot non-default prefix_chars
    # in the consuming ArgumentParser.
    prefix_chars = kwds.pop('prefix_chars', '-')

    # extract specific keywords from kwds, applying passed defaults
    dest    = kwds.pop('dest', dest)

    if any((arg[0] in prefix_chars) for arg in args):
        # switch arg
        nargs = '+'
        kwds['dest'] = dest
    else:
        # positional arg
        nargs = '*'
        # DON'T set kwds['dest']: add_argument() uses the arg name as dest,
        # and raises an error if you also pass dest=.

    nargs   = kwds.pop('nargs', nargs)
    default = kwds.pop('default', default)
    metavar = kwds.pop('metavar', metavar)
    help    = kwds.pop('help', help.format(metavar=metavar))

    parser = ArgumentParser(add_help=False, prefix_chars=prefix_chars)
    parser.add_argument(nargs=nargs,
                        default=default,
                        metavar=metavar,
                        help=help,
                        *args, **kwds)
    return parser

# ****************************************************************************
#   Processing functions for expanding file_arg(), dir_arg(), tree_arg(),
#   file_or_dir_arg(), file_or_tree_arg()
# ****************************************************************************
def files_from(args=None, *,
               ignore_dirs=IGNORE_DIRS,
               # remaining keyword-only arg names intentionally same as 'dest' defaults
               files=None, dirs=None, files_or_dirs=None, trees=None,
               files_or_trees=None):
    """
    files_from() generates the files specified by the arguments -- either
    retrieved from an argparse.ArgumentParser.parse_args() namespace object,
    or passed explicitly as keyword arguments.

    files_from() can be called in either of two ways (or a mix).

    Say you instantiated an argparse.ArgumentParser, passing as parents=[] one
    or more of file_arg(), dir_arg(), file_or_dir_arg(), file_or_tree_arg(),
    tree_arg(). You called its parse_args() method and captured the returned
    namespace object as 'args'.

    You may simply call files_from(args) (or files_from(args=args)). From
    that namespace object files_from() retrieves the user's arguments from
    the (subset of) ArgumentParsers specified by your ArgumentParser's parents.
    The namespace attributes it queries are the default 'dest' values for the
    mumble_arg() functions above.

    Or, if you chose to override dest= when calling the above functions, you
    may instead explicitly pass keyword arguments corresponding to each kind
    of argument.

    When you pass both 'args' and some subset of keyword arguments, an
    explicit keyword argument overrides retrieving the corresponding attribute
    from 'args'. So you can pass keyword arguments for switches whose 'dest'
    you've overridden, while letting files_from() retrieve from 'args' any
    switches whose 'dest' is default.

    files_from() does not depend in any way on ArgumentParser functionality.
    Passing only keyword arguments simply expands the passed iterables
    according to the semantics of the keyword. An 'args' argument is only used
    with getattr().

    ignore_dirs must be an iterable of directory names into which 'trees' or
    'files_or_trees' will never traverse. It's intended for version-control
    hidden directories and such.
    """
    # Capture explicit keyword arguments (excluding 'args' and 'ignore_dirs').
    kwds = locals().copy()
    kwds.pop('args')
    kwds.pop('ignore_dirs')

    # Extract to kwds any namespace attribute not explicitly overridden in kwds.
    for key, value in tuple(kwds.items()):
        if value is None:
            # Typical caller specifies a subset of our mumble_arg() functions
            # as ArgumentParser(parents=), so it's okay if 'args' doesn't have
            # this 'key' as an attribute. This handles even the case when args
            # is (default) None.
            kwds[key] = getattr(args, key, ())

    # Done looking at 'args'. At this point every value in kwds should be an
    # iterable instead of None.

    # Expand files, dirs and trees from wildcards to specific pathnames.
    # Previously we attempted to use Path('.').glob(wild) for this -- but that
    # doesn't support '.' or an absolute pathname. glob.glob() supports both.
    # Moreover, Path('.').glob('*') returns (e.g.) '.git' and '.hg', where
    # glob.glob('*') does not.
    # https://github.com/python/cpython/issues/70284
    # We assume our caller never wants to recur into version-control system
    # repository directories.
    # Because we also support files_or_dirs and files_or_trees, assume that a
    # wildcard in files should match *only* files. Similarly, a wildcard in
    # dirs or trees should match only directories.
    # Construct files, dirs and trees as lists of generators: lists so we can
    # append additional generators before flattening.
    files = [(Path(f) for f in glob.glob(wild) if os.path.isfile(f))
             for wild in kwds['files']]
    dirs  = [(Path(d) for d in glob.glob(wild) if os.path.isdir(d) and d not in ignore_dirs)
             for wild in kwds['dirs']]
    trees = [(Path(d) for d in glob.glob(wild) if os.path.isdir(d) and d not in ignore_dirs)
             for wild in kwds['trees']]

    # For files_or_dirs and files_or_trees, first expand wildcards and flatten.
    # Reify as tuples because we want to make a couple passes over each.
    files_or_dirs  = tuple(itertools.chain.from_iterable(
        (Path(f_d) for f_d in glob.glob(wild)) for wild in kwds['files_or_dirs']))
    files_or_trees = tuple(itertools.chain.from_iterable(
        (Path(f_t) for f_t in glob.glob(wild)) for wild in kwds['files_or_trees']))

    # Categorize expanded pathnames in files_or_dirs and files_or_trees as
    # files and directories, so we need consider only files, dirs and trees.
    files.extend(((f for f in files_or_dirs  if f.is_file()),
                  (f for f in files_or_trees if f.is_file())))
    dirs .append( (d for d in files_or_dirs  if d.is_dir() and d not in ignore_dirs) )
    trees.append( (d for d in files_or_trees if d.is_dir() and d not in ignore_dirs) )

    # Now that we've teased apart files_or_dirs and files_or_trees, we can
    # ignore them. All we care about now is files, dirs and trees.
    # Each of these is a list of generators; each can be flattened to a single
    # iterable of pathnames with itertools.chain.from_iterable().
    # For files, that's all we need.
    # For dirs,  further enumerate all files
    #            in each directory in the flattened sequence.
    # For trees, walk the whole directory subtree
    #            for each directory in the flattened sequence.
    # Each of the latter two needs to be flattened before chaining into a
    # uniform output stream.
    return itertools.chain(
        itertools.chain.from_iterable(files),
        itertools.chain.from_iterable(
            files_in_dir(dir)
            for dir in itertools.chain.from_iterable(dirs)),
        itertools.chain.from_iterable(
            files_in_tree(dir, ignore_dirs=ignore_dirs)
            for dir in itertools.chain.from_iterable(trees)))

def files_in_dir(dir):
    """
    Generate all the files at top level under specified dir.
    """
    return (f for f in Path(dir).iterdir() if f.is_file())

def files_in_tree(dir, ignore_dirs=IGNORE_DIRS):
    """
    Generate all the files at any depth under specified dir. Do not traverse
    into any directory named in ignore_dirs.
    """
    for basedir, subdirs, files in os.walk(dir):
        for file in files:
            yield os.path.join(basedir, file)

        # This is where os.walk() is better than Path.rglob(): we can actually
        # control the traversal by skipping ignore_dirs. We don't have to
        # waste time traversing into them and then filtering their nested
        # files out of the results.
        # https://github.com/python/cpython/issues/70284
        for dir in ignore_dirs:
            # Instead of first testing whether each directory name in
            # ignore_dirs is actually present in subdirs, it's more Pythonic
            # (efficient), at least according to Alex Martelli, to just call
            # remove() and catch ValueError. Instead of two searches, you need
            # only one.
            try:
                subdirs.remove(dir)
            except ValueError:
                pass
