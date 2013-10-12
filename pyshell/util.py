# -*- coding: utf-8 -*-
# 
#  util.py
#  jaberwocky
#  
#  Created by Jaberwocky on 2012-10-16.
#  Copyright 2012 Jaberwocky. All rights reserved.
# 
"""
.. currentmodule: pyshell.util

:mod:`util` - Utilities
=======================

.. testsetup::
    from pyshell.util import *

.. autofunction::
    force_dir_path
    
.. autofunction::
    collapseuser
    
.. autofunction::
    check_exists
    
.. autofunction::
    warn_exists
    
.. autofunction::
    is_remote_path
    
.. autofunction::
    semiabstractmethod
    
.. autofunction::
    deprecatedmethod
    
.. autofunction::
    func_lineno

.. autofunction::
    ipydb

.. autofunction::
    is_type_factory

.. autofunction::
    query_yes_no

.. autofunction::
    query_string
    
.. autofunction::
    query_select

"""

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)

import os, os.path
import sys
import warnings
import functools
import inspect
import six

try:
    input = raw_input
except NameError:
    pass

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import pkg_resources # pylint: disable = unused-import

def ipydb():
    """Try to use the iPython debugger on program failures."""
    try:
        from IPython.core import ultratb
    except ImportError:
        warnings.warn("Not enabling iPython debugger because"
            " 'ipython' isn't installed!")
    else:
        _file = getattr(sys.modules['__main__'], '__file__', '')
        sys.excepthook = ultratb.ColorTB(color_scheme='Linux', call_pdb=1)
        setattr(sys.modules['__main__'], '__file__', _file)

def is_type_factory(ttype):
    """Return a function which checks if an object can be cast as a given 
    type. Basic usage allows for checking string-casting to a specific type.
    
    :param ttype: Usually a ``type`` but really, any function which takes one
        argument and which will raise a :exc:`ValueError` if that one argument can't be 
        cast correctly.
        
    """
    def is_type(obj): # pylint: disable = missing-docstring
        try:
            ttype(obj)
        except ValueError:
            return False
        else:
            return True
    is_type.__doc__ = "Checks if obj can be *cast* as {!r}.".format(ttype)
    is_type.__hlp__ = "Input must be an {!s}".format(ttype)
    return is_type

def force_dir_path(path):
    """Force the input path to be a directory.
    
    Paths are normalized, and then it is ensured that the
    path ends with a `/`.
    
    Converts `/some//path/here` to `/some/path/here/` and
    `/some//path/here//` to `/some/path/here/`
    """
    path = os.path.normpath(path)
    return path.rstrip("/") + "/"
    
def collapseuser(path):
    """Collapse the username from a path."""
    userpath = os.path.expanduser("~")
    if path.startswith(userpath):
        relpath = os.path.relpath(path, userpath)
        return os.path.normpath(os.path.join("~", relpath))
    else:
        return path
    
def join(*args):
    """Join and expand user."""
    return os.path.expanduser(os.path.join(*args))
    
def check_exists(path):
    """Check whether the given directory exists."""
    return os.path.exists(os.path.expanduser(path))
    
def warn_exists(path, name="path", exists=True):
    """Warn if the file path does or does not exist.
    
    :param path: The path to search for.
    :param name: The textual name to use in output.
    :param exists: Whether the filepath **should** exist or not.
    
    """
    if check_exists(path) != exists:
        warnings.warn("{name} '{path}' does{exist} exist!".format(
            name=name.capitalize(), path=path,
            exist=" not" if exists else ""), RuntimeWarning)
            
def remove(path, warn=False, name='path'):
    """docstring for remove"""
    if os.path.exists(path):
        os.remove(path)
    elif warn:
        warnings.warn("{name} '{path}' does not exist!".format(
            name=name.capitalize(), path=path
        ))
    
def is_remote_path(path):
    """Path looks like an SSH or other URL compatible path?"""
    base = path.split("/")[0]
    return ":" in base
    
def func_lineno(func):
    """Get the line number of a function. First looks for
    compat_co_firstlineno, then func_code.co_first_lineno.
    """
    try:
        return six.get_function_code(func).co_firstlineno
    except AttributeError:
        return -1

def semiabstractmethod(txt):
    """Convert semi-abstract-methods into raisers for NotImplementedErrors
    
    .. doctest::
    
        >>> @semiabstractmethod
        ... def myfunc():
        ...     print "Inside myfunc"
        >>> myfunc()
        NotImplementedError
    
    """
    def decorator(func): # pylint: disable= missing-docstring
        @functools.wraps(func) # pylint: disable = unused-argument
        def raiser(*args, **kwargs): # pylint: disable= missing-docstring
            name = func.__name__
            if inspect.ismethod(func):
                name = ".".join([six.get_method_self(func).__class__.__name__, name])
            msg = txt % (name)
            raise NotImplementedError(msg)
        return raiser
    if callable(txt):
        func = txt
        txt = "Abstract method %s() cannot be called."
        return decorator(func)
    return decorator

def deprecatedmethod(message=None, version=None, replacement=None):
    """Mark a method as deprecated.
    
    :param message: The warning message to display, or None.
    :param version: The deprication version. Will be appended to the message.
    :param replacement: A string describing the text to replace.
    
    The final :exc:`DepricationWarning` message is formatted as follows::
        
        "Method {method} will be depricated in version {version}, please use {replacement} instead."
    
    Setting the `message` argument replaces the string ``"Method {method} will be depricated"``.
    """
    def decorator(func): # pylint: disable = missing-docstring
        try:
            txt.format(method=func.__name__)
        except KeyError:
            pass
        @functools.wraps(func)
        def warner(*args, **kwargs): # pylint: disable = missing-docstring
            warnings.warn(txt, DeprecationWarning)
            return func(*args, **kwargs)
        return warner
    if callable(message) or message is None:
        txt = "Method {method} will be deprecated"
    else:
        txt = message
    if version is not None:
        txt += " in version {}".format(version)
    else:
        txt += " soon"
    if replacement is not None:
        txt += " please use {} instead".format(replacement)
    txt += "."
    if callable(message):
        return decorator(message)
    return decorator

# Borrowed from:
# http://stackoverflow.com/questions/3041986/python-command-line-yes-no-input  
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    :param question: A string presented to the user
    :param default: The answer if the user hits <Enter> with no input.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).
    :param output: The output stream.
    :return: `True` or `False` for "yes" or "no" respectively.
    
    """
    valid = {"yes":True, "y":True, "ye":True,
             "no":False, "n":False}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        choice = input(question + prompt).lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")
                             
def query_string(question, default=None, validate=None, output=sys.stdout):
    """Ask a question via raw_input, and return the answer as a string.
    
    :param question: A string presented to the user
    :param default: The answer if the user hits <Enter> with no input.
    :param validate: A function to validate responses. To validate that the answer is a specific type, use :func:`is_type_factory`.
    :param output: The output stream.
    :return: A string with the user's answer or the default if no answer.
    
    """
    
    if default is None:
        prompt = ": "
    else:
        prompt = " ({:s}): ".format(default)
    
    
    while True:
        answer = input(question + prompt)
        if default is not None and answer == '':
            answer = default
        if validate is None or validate(answer):
            return answer
        else:
            if hasattr(validate, '__hlp__'):
                output.write(validate.__hlp__+"\n")
            elif hasattr(validate, '__doc__'):
                output.write("Invalid input, the validation function"
                " has the following documentaion:\n"+validate.__doc__+"\n")
            output.write("Invalid input. Please try again.\n")
            
def query_select(iterable, labels=None, default=None, 
    before="Select from:", question="Select an item", output=sys.stdout):
    """A simple CLI UI to let the user choose an item from a list of items.
    
    :param iterable: The list from which to choose.
    :param labels: The labels for the list from which to choose.
    :param default: The index of the default item in `iterable`
    :param before: The string to print before the choice list.
    :param question: The question to use as the prompt.
    :param output: The output stream.
    """
    
    if labels is None:
        labels = iterable
    elif len(labels) != len(iterable):
        raise ValueError("Labels must be the same length as the iterable.")
    
    def validate(answer):
        valid = is_type_factory(int)(answer)
        if valid:
            valid &= int(answer) <= len(iterable)
            valid &= int(answer) >= 1
        return valid
    
    validate.__hlp__ = "Selection must be an integer between {:d} and {:d}".format(1,len(iterable))
    
    # String Formatting Tools
    line_template = "{number:{indent:d}d}) {text:s}"
    indent = len("{:d}".format(len(iterable)))
    
    output.write(before)
    output.write("\n")
    
    for i,item in enumerate(labels):
        line = line_template.format(number=i+1, indent=indent, text=item)
        output.write(line)
        output.write("\n")
    
    answer = query_string(question, default=default, validate=validate)
    index = int(answer) - 1
    return iterable[index]
            