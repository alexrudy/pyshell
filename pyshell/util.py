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
    semiabstractmethod
    
.. autofunction::
    func_lineno

.. autofunction::
    query_yes_no

.. autofunction::
    query_string

"""
import os
import sys
import warnings
import functools

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
    """docstring for join"""
    args = list(args)
    path = args.pop(0)
    for arg in args:
        path = os.path.join(path, arg)
    return os.path.expanduser(path)
    
def check_exists(path):
    """Check whether the given directory exists."""
    return os.path.exists(os.path.expanduser(path))
    
def warn_exists(path, name="path", exists=True):
    """docstring for warn_exists"""
    if check_exists(path) != exists:
        warnings.warn("{name} '{path}' does{exist} exist!".format(
            name=name.capitalize(), path=path,
            exist=" not" if exists else ""), RuntimeWarning)
    
def is_remote_path(path):
    """Path looks like an SSH or other URL compatible path?"""
    base = path.split("/")[0]
    return ":" in base
    
def func_lineno(func):
    """Get the line number of a function. First looks for
    compat_co_firstlineno, then func_code.co_first_lineno.
    """
    try:
        return func.compat_co_firstlineno
    except AttributeError:
        pass
    try:
        return func.func_code.co_firstlineno
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
            if hasattr(func, 'im_class'):
                name = ".".join([func.im_class.__name__, name])
            msg = txt % (name)
            raise NotImplementedError(msg)
        return raiser
    if callable(txt):
        func = txt
        txt = u"Abstract method %s() cannot be called."
        return decorator(func)
    return decorator

def deprecatedmethod(message=None, version=None, replacement=None):
    """Mark a method as deprecated"""
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
        txt += "in version {}".format(version)
    else:
        txt += "soon"
    if replacement is not None:
        txt += "please use {} instead".format(replacement)
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
    :return: `True` or `False` for "yes" or "no" respectively.
    
    """
    valid = {"yes":True,   "y":True,  "ye":True,
             "no":False,     "n":False}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "\
                             "(or 'y' or 'n').\n")
                             
def query_string(question, default=None, validate=None):
    """Ask a question via raw_input, and return the answer as a string.
    
    :param question: A string presented to the user
    :param default: The answer if the user hits <Enter> with no input.
    :return: A string with the user's answer or the default if no answer.
    
    """
    
    if default is None:
        prompt = " : "
    else:
        prompt = " (%s): " % default
    
    
    while True:
        sys.stdout.write(question + prompt)
        answer = raw_input()
        if default is not None and answer == '':
            answer = default
        if validate is None or validate(answer):
            return answer
        else:
            if hasattr(validate, '__hlp__'):
                sys.stdout.write(validate.__hlp__+"\n")
            elif hasattr(validate, '__doc__'):
                sys.stdout.write("Invalid input, the validation function"
                " has the following documentaion:\n"+validate.__doc__+"\n")
            sys.stdout.write("Invalid input. Please try again.\n")
            