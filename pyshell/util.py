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

"""

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)

import os, os.path
import sys
import warnings
import functools
import inspect
import six
import collections
import argparse

try:
    input = raw_input
except NameError:
    pass

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import pkg_resources # pylint: disable = unused-import

_ipydb_active = False

def ipydb():
    """Try to use the iPython debugger on program failures."""
    global _ipydb_active
    if _ipydb_active:
        return
    
    try:
        from IPython.core import ultratb
    except ImportError:
        warnings.warn("Not enabling iPython debugger because"
            " 'ipython' isn't installed!")
    else:
        _file = getattr(sys.modules['__main__'], '__file__', '')
        sys.excepthook = ultratb.ColorTB(color_scheme='Linux', call_pdb=1)
        setattr(sys.modules['__main__'], '__file__', _file)
        __ipydb_active = True
        
class ipydbAction(argparse._StoreTrueAction):
    """An action which triggers the ipython debugger."""
    
    def __call__(self, parser, namespace, values, option_string):
        """Parse this action. The value is applied to both the namespace and the configuration."""
        ipydb()
        setattr(namespace, self.dest, values)
        

def askip(pylab=False, enter="Launch iPython?", exit="Continuing...", default="no"):
    """Ask for ipython, returning a callable to start the shell, or do nothing.
    
    To ensure that this method is run in the correct scope, it should be called like this::
        
        >>> a = 10
        >>> askip()()
        >>> b = 20 + a
        
    :param bool pylab: Whether to set up interactive pylab plotting.
    :param str enter: Message used as the question to the user.
    :param str exit: Message used when the user exits the shell.
    :param str default: The default answer ("yes" or "no")
    :returns: A function which either does nothing, or starts an iPython shell.
    """
    from IPython.terminal.embed import InteractiveShellEmbed
    if query_yes_no(enter,default=default):
        if pylab:
            import matplotlib.pyplot as plt
            plt.ion()
        return InteractiveShellEmbed(exit_msg=exit)
    else:
        return lambda : None #No-op callable.
        
def resolve(name):
    """Resolve a dotted name to a global object."""
    name = name.split('.')
    used = name.pop(0)
    found = __import__(used)
    for n in name:
        used = used + '.' + n
        try:
            found = getattr(found, n)
        except AttributeError:
            __import__(used)
            found = getattr(found, n)
    return found

def configure_class(configuration):
    """Resolve and configure a class."""
    if isinstance(configuration, six.string_types):
        class_obj = resolve(configuration)()
    elif isinstance(configuration, collections.MutableMapping):
        if "()" in configuration:
            class_type = resolve(configuration.pop("()"))
            class_obj = class_type(**configuration)
        else:
            raise ValueError("Must provide class name in key '()'")
    else:
        raise ValueError("Can't understand {}".format(configuration))
    return class_obj

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

def is_type(instance, ttype):
    """Tests whether an instance is of a current type."""
    return is_type_factory(ttype)(instance)

def force_dir_path(path):
    """Force the input path to be a directory.
    
    Paths are normalized, and then it is ensured that the
    path ends with a `/`.
    
    Converts `/some//path/here` to `/some/path/here/` and
    `/some//path/here//` to `/some/path/here/`
    """
    path = os.path.normpath(path)
    dirpath = path.rstrip(os.path.sep) + os.path.sep
    return dirpath
    
def collapseuser(path):
    """Collapse the username from a path."""
    userpath = os.path.abspath(os.path.expanduser("~"))
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
    """A silent remove."""
    try:
        os.remove(path)
    except OSError:
        if warn:
            warnings.warn("{name} '{path}' does not exist!".format(
                name=name.capitalize(), path=path
            ))
    
def is_remote_path(path):
    """Path looks like an SSH or other URL compatible path?"""
    base = path.split(os.path.sep)[0]
    return (":" in base)
    
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

def _has_readline():
    """Check for the readline module."""
    try:
        import readline
    except ImportError:
        return False
    else:
        return True

def readline_input(prompt, default="", use_readline=True):
    """Readline-based input with a default value."""
    if not _has_readline() and use_readline:
        warnings.warn("The module 'readline' is required for default-value string input.")
        use_readline = False
    
    if use_readline:
        import readline
        readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        result = input(prompt)
    finally:
        if use_readline:
            readline.set_startup_hook()
    return result

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
                             
def query_string(question, default=None, validate=None, process=None, typed=None, output=sys.stdout):
    """Ask a question via raw_input, and return the answer as a string.
    
    :param question: A string presented to the user
    :param default: The answer if the user hits <Enter> with no input.
    :param validate: A function to validate responses. To validate that the answer is a specific type, use :func:`is_type_factory`.
    :param process: Process output from the query before returning.
    :param typed: If a type, uses :func:`is_type_factory` and ensures the result is returned as the correct type.
    :param output: The output stream.
    :return: A string with the user's answer or the default if no answer.
    
    """
    
    if typed is not None:
        if validate is not None or process is not None:
            warnings.warn("[query_string] Ignoring 'typed' keyword because 'validate' or 'process' is set.")
        else:
            validate = is_type_factory(typed)
            process = typed
    
    if default is None:
        prompt = ": "
    elif _has_readline():
        prompt = ":"
    else:
        prompt = " ({:s}): ".format(default)
    
    
    while True:
        answer = readline_input(question + prompt, default=default, use_readline=_has_readline())
        if default is not None and answer == '':
            answer = default
        if validate is None or validate(answer):
            if callable(process):
                answer = process(answer)
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
    
def setup_kwargs(func, *source_kwargs):
    """Set up keyword arguments, pulling from each dictionary successively.
    
    This function uses introspection to build up a set of keyword arguments. Using introspection, it finds the available keyword
    arguments, and gathers values for them from any member in `*source_kwargs`. This function is designed to populate default-valued
    arguments from a list of dictionaries. It does not modify any ``**`` arguments.
    
    :param func: The function to inspect for arguments.
    :param *source_kwargs: Any number of dictionaries to be used to populate the keyword arguments.
    :returns: A dictionary for use with the ``**`` operator as a set of keyword arguments.
    """
    args, varargs, keywords, defaults = inspect.getargspec(func)
    kwargs = {}
    for i,arg in enumerate(args[-len(defaults):]):
        for skw in source_kwargs:
            if arg in skw:
                kwargs[arg] = skw[arg]
                break
        kwargs.setdefault(arg,defaults[i])
    return kwargs
    
def get_keyword_args(func):
    """Get a list of the keyword arguments and their values for a function."""
    args, varargs, keywords, defaults = inspect.getargspec(func)
    kwargs = {}
    for i,arg in enumerate(args[-len(defaults):]):
        kwargs[arg] = defaults[i]
    return kwargs
    
def descriptor__get__(f):
    """A simple wrapper for descriptors which handles the convention that 
    type(self).item should return the full descriptor class used by item."""
    
    @functools.wraps(f)
    def get(self, obj, objtype):
        if obj is None:
            return self
        else:
            return f(self, obj, objtype)
    
    return get
    
class ResetTypedProperty(object):
    """A symbol used to reset a typed property."""
    pass
        
    
class TypedProperty(object):
    """A typed property object."""
    def __init__(self, name, property_class, readonly=False, init_func=None, coerce=False, allow_none=False, init_none=False):
        super(TypedProperty, self).__init__()
        self._class = property_class
        self.name = name
        self._attr = "_{}_{}".format(self.__class__.__name__,name)
        self.readonly = readonly
        self.coerce = coerce
        self.allow_none = allow_none
        if init_none and init_func is None:
            init_func = lambda : None
        elif not readonly and init_func is not None:
            raise ValueError("{} cannot use an intialization function when not a read-only property!".format(self.name))
        self._init_func = init_func
        
    
    @descriptor__get__
    def __get__(self, obj, objtype):
        """Property getter."""
        if (self._init_func is not None) and not hasattr(obj, self._attr):
            setattr(obj, self._attr, self._init_func())
        return getattr(obj, self._attr)
        
    def __set__(self, obj, value):
        """Property setter with type checking."""
        if value is None and not isinstance(value, self._class) and not self.allow_none:
            return
        if value is ResetTypedProperty:
            if hasattr(obj, self._attr):
                delattr(obj, self._attr)
            return
        if hasattr(obj, self._attr) and self.readonly:
            raise AttributeError("{}.{} can't set a read-only attribute".format(obj, self.name))
        if not isinstance(value, self._class):
            if self.coerce:
                try:
                    value = self._class(value)
                except TypeError as e:
                    raise TypeError("{}.{} must be able to create type {}, got {}, exception {}".format(
                        type(obj), self.name, self._class, type(value), e.msg
                    ))
            else:
                raise TypeError("{}.{} requires type {}, got {}".format(type(obj), self.name, self._class, type(value)))
        setattr(obj, self._attr, value)
    

def apply_monkey_patch(base, new, prefix="_original_"):
    """Apply a monkey patch to the target, returning the old."""
    new_name = new.__name__
    old_name = prefix + new_name
    setattr(base, old_name, getattr(base, new_name))
    setattr(base, new_name, new)
    return getattr(base, old_name)

