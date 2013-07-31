# -*- coding: utf-8 -*-
# 
#  config.py
#  AstroObject
#  
#  Created by Alexander Rudy on 2012-02-08.
#  Copyright 2012 Alexander Rudy. All rights reserved.
#  Version 0.6.0
# 
"""
:mod:`config` — YAML-based Configuration Dictionaries
==========================================================

.. testsetup ::
    
    from pyshell.config import *

This module provides structured, YAML based, deep dictionary configuration 
objects. The objects have a built-in deep-update function and use deep-update 
behavior by default. They act otherwise like dictionaries, and handle thier 
internal operation using a storage dictionary. The objects also provide a 
YAML configuration file reading and writing interface.
 
.. inheritance-diagram::
    pyshell.config.Configuration
    pyshell.config.StructuredConfiguration
    :parts: 1
    
.. autofunction::
    pyshell.config.reformat
    
.. autofunction::
    pyshell.config.force_yaml_unicode

.. autofunction::
    pyshell.config.deepmerge
    
.. autofunction::
    pyshell.config.advanceddeepmerge
    

Basic Configurations: :class:`Configuration`
--------------------------------------------

.. autoclass::
    pyshell.config.Configuration
    :members:

Dotted Configurations: :class:`Configuration`
---------------------------------------------

.. autoclass::
    pyshell.config.DottedConfiguration
    :members:
    :inherited-members:


Structured Configurations: :class:`StructuredConfiguration`
-----------------------------------------------------------

.. autoclass::
    pyshell.config.StructuredConfiguration
    :members:
    :inherited-members:


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

# Submodules from this system
from . import util
from . import loggers

#pylint: disable=R0904

__all__ = ['reformat', 'advanceddeepmerge', 'deepmerge',
    'ConfigurationError',
    'Configuration', 'DottedConfiguration', 'StructuredConfiguration']

def force_yaml_unicode():
    """This method forces the PyYAML library to construct unicode objects when
     reading YAML instead of producing regular strings.
    
    It is designed to imporove compatibility in Python2.x using unicode 
    objects.
    """
    from yaml import Loader, SafeLoader

    def construct_yaml_str(self, node):
        """Constructs a regular scalar instead of a python
        string object from a YAML key, forcing all YAML strings
        to be unicode objects."""
        return self.construct_scalar(node)
    Loader.add_constructor('tag:yaml.org,2002:str', construct_yaml_str)
    SafeLoader.add_constructor('tag:yaml.org,2002:str', construct_yaml_str)
    
    
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
            and not isinstance(v, (str, unicode)) ):
            e[k] = [ reformat(i, nt) for i in v ]
        else:
            e[k] = v
    return e
    
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
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = advanceddeepmerge(d.get(k, s()), v, s, sequence, invert, inplace)
            e[k] = r
        elif (sequence and isinstance(v, collections.Sequence) and
            isinstance(d.get(k, None), collections.Sequence) and not
            (isinstance(v, (str, unicode)) or 
            isinstance(d.get(k, None), (str, unicode)))):
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
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = deepmerge(d.get(k, s()), v, s, invert=invert, inplace=inplace)
            e[k] = r
        elif invert:
            e[k] = d.get(k, v)
        else:
            e[k] = u[k]
    return e

class ConfigurationError(Exception):
    """Configuration error"""
    def __init__(self, expected, config=None):
        self.expected = expected
        self.config = config
        self.message = "Expected {key!r} in {config!r}!".format(
            key=self.expected, config=self.config)
        super(ConfigurationError, self).__init__(self.message)
        
class DeepNestDict(dict):
    """Class for deep nestinging emptiness"""
    pass
        

class MutableMappingBase(collections.MutableMapping):
    """Base class for mutable mappings which store things in an internal dictionary"""
    def __init__(self, *args, **kwargs):
        super(MutableMappingBase, self).__init__()
        self.log = loggers.getLogger(self.__module__)
        self._store = self._dt(*args,**kwargs)
        
    __metaclass__ = abc.ABCMeta
    
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
            from cStringIO import StringIO
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


class Configuration(MutableMappingBase):
    """Adds extra methods to dictionary for configuration"""
    def __init__(self, *args, **kwargs):
        super(Configuration, self).__init__(*args, **kwargs)
        self._filename = None
        self._strict = False
        self._dn = self.__class__
    
    _strict = False
    """Whether to use strict lookup controls.""" #pylint: disable=W0105
    
    _dn = DeepNestDict
    """Deep nesting dictionary setting. This class will be used to create 
    deep nesting structures for this dictionary.""" #pylint: disable=W0105
    
    @property
    def dn(self):
        """Deep nesting attribute reader""" #pylint: disable=C0103
        return self._dn
    
    @dn.setter
    def dn(self, new_type):
        """Deep nesting type setter.""" #pylint: disable=C0103
        if not issubclass(new_type, collections.MutableMapping):
            raise ValueError("Deep nesting type must be an instance of {:s}, got {:s}".format(
                collections.MutableMapping, new_type
            ))
        self._dn = new_type
    
    _dt = dict
    """Exctraction nesting dictionary setting. This class will be used to 
    create deep nesting structures when this object is 
    extracted.""" #pylint: disable=W0105
    
    @property
    def dt(self):
        """Deep storage type."""
        return self._dt
        
    @dt.setter
    def dt(self, new_type):
        """Set the deep storage type"""
        self.renest(new_type)
        
    
    name = "Configuration"
    """The name/type of this configuration."""
        
    @property
    def hash(self):
        """Return the HexDigest hash"""
        self._hash = hashlib.md5()
        self._hash.update(str(self))
        return self._hash.hexdigest()
        
    @property
    def filename(self):
        """The filename which has been used to save/load this configuration 
        most recently"""
        return self._filename
    
    
    def __getitem__(self, key):
        """Dictionary getter"""
        rval = self._store.__getitem__(key)
        if isinstance(rval, collections.MutableMapping):
            return self.dn(rval)
        else:
            return rval
    
    def update(self, other, deep=True): #pylint: disable=W0221
        """Update the dictionary using :meth:`merge`.
        
        :param dict-like other: The other dictionary to be merged.
        :param bool deep: Whether to use deep merge (:meth:`merge`) or 
            shallow update.
        
        """
        if deep:
            self.merge(other)
        else:
            self._store.update(other)
    
    def merge(self, other):
        """Merge another configuration into this one (the master).
        
        :param dict-like other: The other dictionary to be merged.
        
        See :func:`deepmerge`.
        
        .. doctest::
            
            >>> a = Configuration(**{'a':'b','c':'e'})
            >>> a.merge({'c':'d'})
            >>> a
            {'a': 'b', 'c': 'd'}
        
        """
        deepmerge(self, other, self.dt)
        
    def imerge(self, other):
        """Inverse :meth:`merge`, where ``other`` will be considered original, and this object will be canonical.
        
        :param dict-like other: The other dictionary to be merged.
        
        See :func:`deepmerge`.
        
        .. doctest::
            
            >>> a = Configuration(**{'a':'b','c':'e'})
            >>> a.imerge({'c':'d'})
            >>> a
            {'a': 'b', 'c': 'e'}
        
        """
        deepmerge(self, other, self.dt, invert=True)
        
    
    def save(self, filename, silent=True):
        """Save this configuration as a YAML file. YAML files generally have 
        the ``.yaml`` or ``.yml`` extension. If the filename ends in 
        ``.dat``, the configuration will be saved as a raw dictionary literal.
        
        :param string filename: The filename on which to save the configuration.
        :param bool silent: Unused.
        
        """
        if hasattr(filename,'read') and hasattr(filename,'readlines'):
            filename.write("# %s: <stream>" % self.name)
            yaml.safe_dump_all(self._save_yaml_callback() + [self.store],
                 filename, default_flow_style=False, encoding='utf-8')
        else:
            with open(filename, "w") as stream:
                stream.write("# %s: %s\n" % (self.name, filename))
                if re.search(r"(\.yaml|\.yml)$", filename):
                    yaml.safe_dump_all(
                        self._save_yaml_callback() + [self.store], stream, 
                        default_flow_style=False, encoding='utf-8')
                elif re.search(r"\.dat$", filename):
                    for document in self._save_yaml_callback():
                        stream.write(str(document))
                        stream.write("\n---\n")
                    stream.write(str(self.store))
                elif not silent:
                    raise ValueError("Filename Error, not "
                        "(.dat,.yaml,.yml): %s" % filename)
            self._filename = filename
        
    def load(self, filename, silent=True, fname=None):
        """Loads a configuration from a yaml file, and merges it into 
        the master configuration.
        
        :param string filename: The filename to load from.
        :param bool silent: Silence IOErrors which might arise due to a 
            non-existant configuration file. If this is the case, the failure 
            to find a configuration file will be logged, will not raise an 
            error.
        :raises: :exc:`IOError` if the file can't be found.
        :returns: boolean, whether the file was loaded.
        """
        loaded = False
        isstream = False
        try:
            if hasattr(filename, 'read') and hasattr(filename, 'readlines'):
                new = list(yaml.load_all(filename))
                isstream = True
            else:
                with open(filename, "r") as stream:
                    new = list(yaml.load_all(stream))
        except IOError:
            if silent:
                warnings.warn("Could not load configuration "
                    "from file: %s" % filename, UserWarning)
            else:
                raise
        else:
            if len(new) != 0:
                self.merge(new[-1])
            if isstream and fname is not None:
                self._filename = fname
            elif isstream and hasattr(filename,'name'):
                self._filename = filename.name
            elif not isstream:
                self._filename = filename
            self._load_yaml_callback(*new[:-1])
            loaded = bool(len(new))
        return loaded
    
    def _load_yaml_callback(self,*documents):
        """Called with the extra documents that were loaded from the yaml file."""
        if len(documents) != 0:
            filename = self._filename if self._filename is not None else "<stream>"
            warn("'{:s}' contained {:d} YAML documents. Ignoring all but the last one.".format(filename,len(documents)+1))
    
    def _save_yaml_callback(self):
        """This function should return other yaml documents that will be prepended to the master YAML file."""
        return []
    
    @property
    def store(self):
        """Dictionary representing this configuration. This property should 
        be used if you wish to have a 'true' dictionary object. It is used 
        internally to write this configuration to a YAML file.
        """
        return reformat(self._store, self.dt)
    
    def renest(self, deep_store_type=None):
        """Re-nest this object. This method applies the 
        :attr:`dt` deep-storage attribute to each nesting level in the 
        configuration object.
        
        :param deep_store_type: mapping nesting type, will set :attr:`dn`.
        
        This method does not return anything.
        """
        if deep_store_type is not None and issubclass(deep_store_type, collections.Mapping):
            self._dt = deep_store_type #pylint: disable=C0103
        elif deep_store_type is not None:
            raise TypeError("%r is not a mapping type." % deep_store_type)
        self._store = reformat(self._store, self.dt)
        
    def parse_literals(self, *literals, **kwargs):
        """Turn a list of literals into configuration items.
        
        :param literals: Any literals which are separated by the separator.
        :keyword sep: The separator to use, defaults to ``"="``.
        
        Keywords are parsed where ``foo=bar`` becomes ``self["foo"] = "bar"``.
        If ``bar`` can be parsed as a python literal (float, int, dict, list 
        etc..), the literal value will be used in place of the string. 
        For which literals will be parsed, see :func:`ast.literal_eval` from
        the Abstract-Syntax Tree features in python. There is great power in
        using this method with dotted configurations, as ``foo.bat=bar`` will
        get parsed to  ``self["foo.bat"] = "bar"``.  This is useful for 
        parsing configuration command line options.
        
        """
        for item in literals:    
            parts = item.split(kwargs.pop('sep', "="), 1)
            if len(parts) != 2:
                raise ValueError("Invalid literal: %s" % item)
            else:
                key, value = parts
            try:
                self[key] = ast.literal_eval(value)
            except ValueError:
                self[key] = value
        
    def load_resource(self, module, filename, silent=True):
        """Load from a resource filename"""
        from pkg_resources import resource_stream
        try:
            with resource_stream(module, filename) as stream:
                self.load(stream, fname=filename, silent=silent)
        except IOError:
            if silent:
                warn("Resource ({},{}) does not exist.".format(
                    module, filename
                ))
            else:
                raise
        
        
    def configure(self, module=__name__, defaultcfg=False,
        cfg=False, supercfg=None):
        """The configuration loads (starting with a blank configuration):
        
            1. The list of ``supercfg`` 's. This list should contain tuples 
               of ``(module,name)`` pairs.
            2. The ``module`` configuration file named for ``defaultcfg``
            3. The ``cfg`` file from the user's home folder ``~/config.yml``
            4. The ``cfg`` file from the working directory.
        
        If the fourth file is not found, and the user specified a new name 
        for the configuration file (i.e. ``cfg != defaultcfg``), then the 
        user is warned that no configuration file could be found. This way 
        the user is only warned about a missing configuration file if they 
        requested a file specifically (and so intended to use a 
        customized file).
        
        :param string module: The name of the module for searching for the 
            default config.
        :param string cfg: The name of the requested configuration file.
        :param string defaultcfg: The name of the default configuration 
            file which might exist in the module's file.
        :param list supercfg: A list of configuration files to preload. The 
            list should contian pairs of ``(module,name)`` as tuples.
        
        """
        if not defaultcfg:
            return
        if supercfg is None:
            supercfg = []
        for supermodule, superfilename in supercfg:
            if supermodule is None:
                self.load(superfilename)
            else:
                self.load_resource(supermodule,superfilename)
        self.load_resource(module, defaultcfg)
        if cfg and util.check_exists("~/%s" % cfg):
            self.load(os.path.expanduser("~/%s" % cfg))
        if cfg and os.path.exists(cfg):
            self.load(cfg, silent=False)
        elif cfg and cfg != defaultcfg:
            warn("Configuration File '{}'"
                " not found!".format(cfg), RuntimeWarning)
        
        
        
    @classmethod
    def create(cls, module=__name__, defaultcfg=False,
        cfg=False, supercfg=None):
        """Create a configuration from a series of YAML files.
        
        See :meth:`configure` for a detailed description of the 
        resolution order of configuration files for this method.
        """
        config = cls()
        config.configure(module, defaultcfg, cfg, supercfg)
        return config
        
    @classmethod
    def fromfile(cls, filename):
        """Create a configuration from a single YAML file."""
        config = cls()
        config.load(filename, silent=False)
        return config
        
    @classmethod
    def fromresource(cls, module, filename):
        """Create a configuration from a resource filename pair.
        
        :param module: The module containing the file.
        :param filename: The filename within that module.
        
        """
        config = cls()
        config.load_resource(module, filename)
        return config
        
    @classmethod
    def make(cls,base):
        """Make a configuration from the input object ``base``.
        
        Acceptable Inputs:
        
        - An instance of this class.
        - Any insatance of :class:`collections.Mapping`
        - A string filename for :meth:`fromfile`
        - A tuple of argumments to :meth:`fromresource`
        - A sequence of arguments to this method, which can be recursively added to this configuration.
        
        """
        if base is None:
            return cls()
        elif isinstance(base,cls):
            return base
        elif isinstance(base,collections.Mapping):
            return cls(base)        
        elif isinstance(base,tuple) and len(base) == 2:
            return cls.fromresource(*base)
        elif isinstance(base,basestring):
            config = cls.fromfile(base)
        elif isinstance(base,collections.Sequence):
            config = cls()
            for item in base:
                config.update(cls.make(item))
            return config
        else:
            raise TypeError("{0} doesn't know how to make from {1}".format(
                cls.__name__, type(base)
            ))



class DottedConfiguration(Configuration):
    """A configuration which can use dotted accessor methods.
    
    Configuration variables can be accessed and set with dot-qualified names. E.g.::
        
        >>> Config = DottedConfiguration( { "Data": { "Value": { "ResultA" : 10 }, }, })
        >>> Config["Data"]["Value"]["ResultA"]
        10
        >>> Config["Data.Value.ResultA"]
        10
        
    By default, this will not work for doubly nested values::
    
        >>> Config["Data"]["Value.ResultA"]
        KeyError
        
    However, this behavior can be changed by specifying a new default nesting structure::
        
        >>> Config.dn = DottedConfiguration
        >>> Config.merge(Config)
        >>> Config["Data"]["Value.ResultA"]
        10
        
    """
    
    def _isempty(self, item):
        """Test if the given item is empty"""
        #pylint: disable=W0703
        try:
            if isinstance(item, collections.Mapping):
                return all([self._isempty(value) 
                    for value in item.itervalues()])
            elif isinstance(item, collections.Sized):
                return len(item) == 0
            else:
                try:
                    return not bool(item)
                except Exception:
                    return False
        except Exception:
            return False
        
    def _getitem(self, store, parts):
        """Recursive getitem calling function."""
        if len(parts) == 0:
            return store
        if not isinstance(store, collections.Mapping):
            raise KeyError
        
        np = len(parts)
        for i in range(np):
            key = ".".join(parts[:np-i])
            if key in store:
                if self._strict and self._isempty(store[key]):
                    raise KeyError
                elif not self._isempty(store[key]):
                    return self._getitem(store[key], parts[np-i:])
        key = parts.pop(0)
        if (not self._strict) and len(parts) != 0:
            store.setdefault(key, self.dt())
        return self._getitem(store[key], parts)
            
    def _setitem(self, store, parts, value=None):
        """Recursive setitem calling function
        
        This function handles a few things:
        - Store is passed in as a variable to make the recursive mode work.
        - If there are no more parts left, then we call the store's setitem.
        - If there are parts left, then we get the value of the next key in line. When we do this, if that key has not been set, we use a default nester, the ``self.dn`` attribute, which should construct a mapping object.
        - Recurses into the system.
        
        """
        key = parts.pop(0)
        if len(parts) == 0:
            return store.__setitem__(key, value)
        elif not self._strict:
            store.setdefault(key, self.dt())
        return self._setitem(store[key], parts, value)
            
    def _delitem(self, store, parts):
        """Recursive delitem calling function"""
        if len(parts) == 1:
            return store.__delitem__(parts[0])
        else:
            np = len(parts)
            for i in range(np):
                key = ".".join(parts[:np-i])
                remain = parts[np-i:]
                if key in store and remain:
                    return self._delitem(store[key], remain)
                elif key in store:
                    return store.__delitem__(key)
            raise KeyError
            
    def _contains(self, store, parts):
        """Recursive containment algorithm"""
        if len(parts) == 0:
            return True
        else:
            np = len(parts)
            for i in range(np):
                key = ".".join(parts[:np-i])
                if key in store:
                    return self._contains(store[key], parts[np-i:])
            return False
        
        
    def __getitem__(self, key):
        """Dictionary getter"""
        keyparts = key.split(".")
        try:
            if len(keyparts) > 1:
                rval = self._getitem(self._store, keyparts)
            elif (self._strict and (isinstance(self._store.get(key), self.dt) 
                and not bool(self._store.get(key)))):
                raise KeyError
            else:
                rval =  self._store[key]
        except KeyError:
            raise KeyError('%s' % key)
        
        if isinstance(rval,collections.MutableMapping):
            return self.dn(rval)
        else:
            return rval
            
        
    def __setitem__(self, key, value):
        """Dictonary setter"""
        keyparts = key.split(".")
        if len(keyparts) > 1:
            return self._setitem(self._store, keyparts, value)
        return self._store.__setitem__(key, value)
        
    def __delitem__(self, key):
        """Dictionary delete"""
        keyparts = key.split(".")
        try:
            if len(keyparts) > 1:
                return self._delitem(self._store, keyparts)        
            return self._store.__delitem__(key)
        except KeyError:
            # raise KeyError('%s' % key)
            raise
        
        
    def __contains__(self, key):
        """Dictionary in"""
        keyparts = key.split(".")
        if len(keyparts) > 1:
            return self._contains(self._store, keyparts)
        elif (self._strict and (isinstance(self._store.get(key), self.dt) 
            and not bool(self._store.get(key)))):
            return False
        else:
            return self._store.__contains__(key)
    


class StructuredConfiguration(DottedConfiguration):
    """A structured configuration with some basic defaults.
    
    This class does two things differently for configurations:
    
    1. Configurations are stored in a "Configurations" variable set. 
       They can then be loaded by configuration key instead of filename, 
       using the :meth:`setFile` method to set the filename, and then 
       calling :meth:`load` or meth:`save` with no arguments.
    2. Configuration variables can be accessed and set with dot-qualified 
       names. E.g.::
        
        >>> Config = StructuredConfigruation( { "Data": { "Value": { "ResultA" : 10 }, }, })
        >>> Config["Data"]["Value"]["ResultA"]
        10
        >>> Config["Data.Value.ResultA"]
        10
        
    
    By default, this will not work for doubly nested values::
        
        >>> Config["Data"]["Value.ResultA"]
        KeyError
        
    However, this behavior can be changed by specifying a new default nesting structure::
        
        >>> Config.dn = DottedConfiguration
        
    """
    
    DEFAULT_FILENAME = '__main__'
    
    def __init__(self,  *args, **kwargs):
        super(StructuredConfiguration, self).__init__(*args, **kwargs)
        self._metadata = DottedConfiguration()
        self._metadata["Files.This"] = self.DEFAULT_FILENAME
        self._metadata["Files.Loaded"] = []
        self._metadata["Configurations"] = self._metadata.dn()
        self.__set_on_load = False
        self._dn = DottedConfiguration
        
    @property
    def metadata(self):
        """The metadata dictionary"""
        self._metadata["Hash"] = self.hash
        return self._metadata
        
    @property
    def files(self):
        """The set of loaded filenames"""
        return set(self._metadata["Files.Loaded"])
        
    @property
    def _set_on_load(self):
        """True for default filenames"""
        if self._metadata["Files.This"] == self.DEFAULT_FILENAME:
            self.__set_on_load = True
        return self.__set_on_load
    
    def set_file(self, filename=None):
        """Set the default/current configuration file for this configuration.
        
        The configuration file set by this method will be used next time :meth:`load` or :meth:`save` is called with no filename.
        
        :param string filename: The filename to load from.
        
        """
        self._metadata["Files.This"] = filename
    
    def save(self, filename=None, silent=True):
        """Save the configuration to a YAML file. If ``filename`` is not 
        provided, the configuration will use the file set by :meth:`setFile`.
        
        :param string filename: Destination filename.
        
        Uses :meth:`Configuration.save`.
        """
        if filename == None:
            filename = self._metadata["Files.This"]
        return super(StructuredConfiguration, self).save(filename)
    
    def _load_yaml_callback(self,*documents):
        """Load the metadata"""
        if len(documents) == 1:
            self._metadata.update(documents[0])
        elif len(documents) > 1:
            self._metadata.update(documents[0])
            warnings.warn("Too Many metadata documents found. Ignoring {:d} documents".format(len(documents)-1))
        
    def _save_yaml_callback(self):
        """Return the metadata in an array."""
        return [ self.metadata.store ]
    
    def load(self, filename=None, silent=True, fname=None):
        """Load the configuration to a YAML file. If ``filename`` is 
        not provided, the configuration will use the file set by 
        :meth:`setFile`.
        
        :param string filename: Target filename.
        :param bool silent: Whether to raise an error if the target file cannot be found.
        
        Uses :meth:`Configuration.load`."""
        if filename == None:
            filename = self._metadata["Files.This"]
        loaded = super(StructuredConfiguration, self).load(filename, silent, fname=fname)
        if loaded and self._set_on_load:
            self._metadata["Files.Loaded"].append(self.filename)
        


force_yaml_unicode()