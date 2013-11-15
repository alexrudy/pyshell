# -*- coding: utf-8 -*-
# 
#  mapping.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-11-13.
#  Copyright 2013 Alexander Rudy. All rights reserved.
# 
"""
:mod:`mapping` – Mutable Mapping Tools
======================================

This module contains functions and base classes for mutable mappings in Python.


Mapping Base Classes
--------------------

.. autoclass::
    pyshell.mapping.MutableMappingBase
    :members:

.. autoclass::
    pyshell.mapping.FallbackDictionary
    :members:


Mapping Functions
-----------------
"""
from __future__ import (absolute_import, unicode_literals, division,
                        print_function)

# Standard Python Modules
import os
import collections
import abc
import re
import yaml
import warnings
import hashlib
from warnings import warn
import ast
import six

# Submodules from this system
from . import util
from . import loggers

#pylint: disable=R0904

__all__ = ['reformat', 'advanceddeepmerge', 'deepmerge','flatten','expand']

def reformat(d, nt):
    """Recursive extraction method for changing the type of 
    nested dictionary objects.
    
    :param mapping d: The dictionary to re-type.
    :param mapping-type nt: The new mapping type to use.
    
    """
    #pylint: disable=C0103
    if not isinstance(d, collections.Mapping):
        return d
    e = nt()
    for k in d:
        v = d.get(k)
        if isinstance(v, collections.Mapping):
            e[k] = reformat(v, nt)
        elif ( isinstance(v, collections.Sequence) 
            and not isinstance(v, six.string_types) ):
            e[k] = [ reformat(i, nt) for i in v ]
        else:
            e[k] = v
    return e
    
def flatten(d, stump="", sequence=False, separator=".", dt=dict):
    """Flatten a given nested dictionary.
    
    :param d: Dictionary to flatten.
    :param stump: The base stump for flattened keys. Setting this applies a universal starting value to each key.
    :param sequence: Whether to expand sequences.
    :param separator: The string separator to use in flat keys.
    :param dt: The final output type for the dictionary.
    
    Each nested key will become a root level key in the final dictionary. The root level keys will be the set of nested keys, joined by the `separator` keyword argument.
    
    """
    o = dt()
    if ( isinstance(d, collections.Sequence)
        and not isinstance(d, six.string_types) and
        sequence):
        for i,iv in enumerate(v):
            o.update(flatten(iv, nk+str(i), sequence, separator))
    elif isinstance(d, collections.Mapping):    
        for k,v in d.items():
            nk = separator.join((stump,k)) if stump else k
            o.update(flatten(v, nk, sequence, separator))
    else:
        o[stump] = d
    return o
    
def expand(d, sequence=False, separator=".", dt=dict):
    """Expand a flattened dictionary into a nested one.
    
    :param d: Dictionary to expand.
    :param sequence: Whether to expand sequences.
    :param separator: The string separator to use in flat keys.
    :param dt: The final output type for all levels of the nested dictionary.
    
    Each key with the `separator` will become a nested dictionary key in the final dictionary."""
    if isinstance(d, collections.Mapping):
        o = dt()
        for k,v in d.items():
            ks = k.split(separator)
            n = o
            for nk in ks[:-1]:
                n = n.setdefault(nk, dt())
            n[ks[-1]] = expand(v, sequence=sequence, separator=separator, dt=dt)
    else:
        o = d
    return o
    
def advanceddeepmerge(d, u, s, sequence=True, invert=False, inplace=True):
    """Merge deep collection-like structures.
    
    This function will merge sequence structures when they are found. When used with ``sequence=False``, it behaves like :func:`deepmerge`.
    
    :param dict-like d: Deep Structure
    :param dict-like u: Updated Structure
    :param dict-like-type s: Default structure to use when a new deep structure is required.
    :param bool sequence: Control sequence merging
    :param bool invert: Whether to do an inverse merge.
    
    *Inverse Merge* causes ``u`` to only update missing values of ``d``, but does
    so in a deep fashion.
    
    """
    #pylint: disable=C0103
    if isinstance(d, collections.Mapping) and not inplace:
        e = type(d)(**d)
    else:
        e = d
    if (not hasattr(u,'__len__')) or len(u)==0:
        return e
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            r = advanceddeepmerge(d.get(k, s()), v, s, sequence, invert, inplace)
            e[k] = r
        elif (sequence and isinstance(v, collections.Sequence) and
            isinstance(d.get(k, None), collections.Sequence) and not
            (isinstance(v, six.string_types) or 
            isinstance(d.get(k, None), six.string_types))):
            if invert:
                e[k] = [ i for i in v ] + [ i for i in d[k] ]
            else:
                e[k] = [ i for i in d[k] ] + [ i for i in v ]
        elif invert:
            e[k] = d.get(k,u[k])
        else:
            e[k] = u[k]
    return e

def deepmerge(d, u, s, invert=False, inplace=True):
    """Merge deep collection-like structures.
    
    When this function encounters a sequence, the entire sequence from ``u`` is considered a single value which replaces any value from ``d``. To allow for merging sequences in ``u`` and ``d``, see function :func:`advanceddeepmerge`.
    
    :param dict-like d: Deep Structure
    :param dict-like u: Updated Structure
    :param dict-like-type s: Default structure to use when a new deep structure is required.
    :param bool invert: Whether to do an inverse merge.
    
    *Inverse Merge* causes ``u`` to only update missing values of ``d``, but does
    so in a deep fashion.
    
    """
    #pylint: disable=C0103
    if isinstance(d, collections.Mapping) and not inplace:
        e = type(d)(**d)
    else:
        e = d
    if (not hasattr(u,'__len__')) or len(u)==0:
        return e
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            r = deepmerge(d.get(k, s()), v, s, invert=invert, inplace=inplace)
            e[k] = r
        elif invert:
            e[k] = d.get(k, v)
        else:
            e[k] = u[k]
    return e
        

@six.add_metaclass(abc.ABCMeta)
class MutableMappingBase(collections.MutableMapping):
    """Base class for mutable mappings which store things in an internal dictionary.
    
    This class implements a full dictionary interface, including pretty-printing,
    containment, setting, deleting and getting of items. The interface works via
    :class:`collections.MutableMapping`. Internally, values are stored in an 'inner'
    mapping object, which is set by the attribute :attr:`_dt`."""
    def __init__(self, *args, **kwargs):
        super(MutableMappingBase, self).__init__()
        if len(args) == 1 and isinstance(args[0],self._dt) and len(kwargs) == 0:
            self._store = args[0]
        self._store = self._dt(*args,**kwargs)
        
    _dt = dict
        
    def __str__(self):
        """String representation of this object"""
        return repr(self.store)
        
    def __repr__(self):
        """String for this object"""
        return "<%s %s>" % (self.__class__.__name__, str(self.store))
        
    def _repr_pretty_(self, p, cycle):
        """Pretty representation of this object."""
        if cycle:
            p.text("{}(...)".format(self.__class__.__name__))
        else:
            with p.group(2,"{}(".format(self.__class__.__name__),")"):
                p.pretty(self.store)
        
    def __getitem__(self, key):
        """Dictionary getter"""
        return self._store.__getitem__(key)
        
    def __setitem__(self, key, value):
        """Dictonary setter"""
        return self._store.__setitem__(key, value)
        
    def __delitem__(self, key):
        """Dictionary delete"""
        return self._store.__delitem__(key)
        
    def __iter__(self):
        """Return an iterator for this dictionary"""
        return self._store.__iter__()
        
    def __contains__(self, key):
        """Return the contains boolean"""
        return self._store.__contains__(key)
    
    def __len__(self):
        """Length"""
        return self._store.__len__()
        
    @property
    def store(self):
        """Return a copy of the internal storage object."""
        return self._store.copy()
        
    def merge(self, item):
        """Alias between merge and update in the basic case."""
        return self._store.update(item)
        
@six.add_metaclass(abc.ABCMeta)
class FallbackDictionary(object):
    """An abstract base class for dictionaries which might not contain all of their desired objects.
    
    Contains abstract methods for accessing missing items.
    """
    
    def __getitem__(self, key):
        """Dictionary getter"""
        if key not in self:
            self.build_key(key)
        return super(FallbackDictionary, self).__getitem__(key)
        
    @abc.abstractmethod
    def build_key(self, key):
        """A custom method to build missing keys for this dictionary."""
        raise KeyError("Fallback undefined!")
        
    
_RECLASS = re.compile("")

class RegexDictionary(object):
    """A dictionary which allows indexing with regular expression objects."""
    
    def find_keys(self, regex):
        """Find a set of keys"""
        return self[re.compile(regex)]
    
    def _matching_keys(self, rexp):
        """Return the keys which match a given regular expression."""
        return tuple([ key for key in self.keys() if rexp.search(key) is not None ])
    
    def __getitem__(self, key):
        """Get an item."""
        if isinstance(key, type(_RECLASS)):
            return tuple([ super(RegexDictionary, self).__getitem__(rkey) for rkey in self._matching_keys(key) ])
        else:
            return super(RegexDictionary, self).__getitem__(key)
        
    def __setitem__(self, key, value):
        """Set an item."""
        if isinstance(key, type(_RECLASS)):
            raise TypeError("Key cannot be a instance of {}".format(type(_RECLASS)))
        else:
            super(RegexDictionary, self).__setitem__(key, value)
        
    def __delitem__(self, key):
        """Delete an item, or a regular expression match of items."""
        if isinstance(key, type(_RECLASS)):
            for rkey in self._matching_keys(key):
                super(RegexDictionary, self).__delitem__(rkey)
        else:
            super(RegexDictionary, self).__delitem__(key)
            
        
    

