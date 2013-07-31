# -*- coding: utf-8 -*-
# 
#  pipelinehelp.py
#  pyshell
#  
#  Created by Alexander Rudy on 2012-11-21.
#  Copyright 2012 Alexander Rudy. All rights reserved.
# 

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)


def optional(optional=True):
    """Makes this object optional. This stage will now trap all exceptions, and will not cause the simulator to fail if it fails."""
    if callable(optional) or optional:
        func = optional
        func.optional = True
        return func
    def decorate(func):
        func.optional = optional
        return func
    return decorate
    
def description(description):
    """Gives this object a description"""
    def decorate(func):
        func.description = description
        return func
    return decorate
    

def include(include=True):
    """Commands this object to be included in the ``*all`` method."""
    if callable(include):
        func = include
        func.include = True
        return func
    def decorate(func):
        func.include = include
        return func
    return decorate

def replaces(*replaces):
    """Registers replacements for this stage. This stage will satisfy any dependencies which call for ``replaces`` if this stage is run before those dependencies are requested."""
    def decorate(func):
        func.replaces = list(replaces)
        return func
    return decorate

def help(help):
    """Registers a help string for this function"""
    def decorate(func):
        func.help = help
        return func
    return decorate

def depends(*dependencies):
    """Registers dependencies for this function. Dependencies will be completed before this stage is called."""
    def decorate(func):
        func.dependencies = list(dependencies)
        return func
    return decorate

def triggers(*triggers):
    """Registers triggers for this function. Triggers are stages which should be added to the run queue if this stage is called."""
    def decorate(func):
        func.triggers = list(triggers)
        return func
    return decorate

def excepts(*exceptions):
    """Registers exceptions for this function. Exceptions listed here are deemed 'acceptable failures' for this stage, and will allow the simulator to continue operating
    without error.
    """
    def decorate(func):
        func.exceptions = tuple(exceptions)
        return func
    return decorate

def collect(collect=True):
    """Include stage explicitly in simulator automated stage collection"""
    if callable(collect):
        func = collect
        func.collect = True
        return func
    def decorate(func):
        func.collect = collect
        return func
    return decorate
    

def ignore(ignore=True):
    """Ignore stage explicitly in simulator automated stage collection"""
    if callable(ignore):
        func = ignore
        func.ignore = True
        return func
    def decorate(func):
        func.ignore = ignore
        return func
    return decorate
    