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

.. autofunction::
    force_dir_path
    
.. autofunction::
    semiabstractmethod
    
.. autofunction::
    func_lineno
    
.. autofunction::
    make_decorator

.. autofunction::
    query_yes_no

.. autofunction::
    query_string

"""
import os
import sys

def force_dir_path(path):
    """Force the input path to be a directory.
    
    Paths are normalized, and then it is ensured that the
    path ends with a `/`.
    
    Converts `/some//path/here` to `/some/path/here/` and
    `/some//path/here//` to `/some/path/here/`
    """
    path = os.path.normpath(path)
    return path.rstrip("/") + "/"
    
def func_lineno(func):
    """Get the line number of a function. First looks for
    compat_co_firstlineno, then func_code.co_first_lineno.
    """
    try:
        return func.func_code.co_firstlineno
    except AttributeError:
        return -1

def make_decorator(func):
    """
    Wraps a test decorator so as to properly replicate metadata
    of the decorated function, including nose's additional stuff
    (namely, setup and teardown).
    """
    def decorate(newfunc):
        if hasattr(func, 'compat_func_name'):
            name = func.compat_func_name
        else:
            name = func.__name__
        newfunc.__dict__ = func.__dict__
        newfunc.__doc__ = func.__doc__
        newfunc.__module__ = func.__module__
        if not hasattr(newfunc, 'compat_co_firstlineno'):
            newfunc.compat_co_firstlineno = func.func_code.co_firstlineno
        try:
            newfunc.__name__ = name
        except TypeError:
            # can't set func name in 2.3
            newfunc.compat_func_name = name
        return newfunc
    return decorate

def semiabstractmethod(txt):
    """Convert semi-abstract-methods into raisers for NotImplementedErrors"""
    if callable(txt):
        func = txt
        txt = u"Abstract method %s.%s() cannot be called."
    def decorator(func):
        def raiser(self, *args, **kwargs):
            msg = txt % (self, func.__name__)
            raise NotImplementedError(msg)
        newfunc = make_decorator(func)(raiser)
        return newfunc
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
            sys.stdout.write("Invalid input. Please try again.\n")
            