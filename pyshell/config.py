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

This module provides structured, YAML based, deep dictionary configuration objects. The objects have a built-in deep-update function and use deep-update behavior by default. They act otherwise like dictionaries, and handle thier internal operation using a storage dictionary. The objects also provide a YAML configuration file reading and writing interface.

.. inheritance-diagram::
    AstroObject.config.Configuration
    AstroObject.config.StructuredConfiguration
    :parts: 1
    
.. autofunction::
    AstroObject.config.reformat

Basic Configurations: :class:`Configuration`
--------------------------------------------

.. autoclass::
    AstroObject.config.Configuration
    :members:

Dotted Configurations: :class:`Configuration`
---------------------------------------------

.. autoclass::
    AstroObject.config.DottedConfiguration
    :members:
    :inherited-members:


Structured Configurations: :class:`StructuredConfiguration`
-----------------------------------------------------------

.. autoclass::
    AstroObject.config.StructuredConfiguration
    :members:
    :inherited-members:


"""
# Standard Python Modules
import os
import collections
import re
import yaml
import logging
import warnings
from warnings import warn


# Submodules from this system
from . import util

__all__ = ['reformat','advanceddeepmerge','deepmerge','ConfigurationError','Configuration','DottedConfiguration','StructuredConfiguration']


def reformat(d,nt):
    """Recursive extraction method for changing the type of nested dictionary objects.
    
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
            e[k] = reformat(v,nt)
        elif isinstance(v, collections.Sequence) and not isinstance(v, (str, unicode)):
            e[k] = [ reformat(i,nt) for i in v ]
        else:
            e[k] = v
    return e
    
def advanceddeepmerge(d,u,s,sequence=True):
    """Merge deep collection-like structures.
    
    This version will merge sequence structures when they are found.
    
    :param d: Deep Structure
    :param u: Updated Structure
    :param s: Default structure to use when a new deep structure is required.
    :param (bool) sequence: Control sequence merging
    
    """
    if len(u)==0:
        return d
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = deepmerge(d.get(k, s()), v, s)
            d[k] = r
        elif sequence and isinstance(v, collections.Sequence) and isinstance(d.get(k,None), collections.Sequence) and not (isinstance(v,(str,unicode)) or isinstance(d.get(k,None),(str,unicode))):
            d[k] = [ i for i in v ] + [ i for i in d[k] ]
        else:
            d[k] = u[k]
    return d

def deepmerge(d,u,s):
    """Merge deep collection-like structures.
    
    :param d: Deep Structure
    :param u: Updated Structure
    :param s: Default structure to use when a new deep structure is required.
    
    """
    if len(u)==0:
        return d
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = deepmerge(d.get(k, s()), v, s)
            d[k] = r
        else:
            d[k] = u[k]
    return d
    

class ConfigurationError(Exception):
    """Configuration error"""
    def __init__(self, expected, config={}):
        self.expected = expected
        self.config = config
        self.message = "Expected {key!r} in {config!r}!".format(key=self.expected,config=self.config)
        super(ConfigurationError, self).__init__(self.message)
        


class Configuration(collections.MutableMapping):
    """Adds extra methods to dictionary for configuration"""
    
    _dn = dict
    """Deep nesting dictionary setting. This class will be used to create deep nesting structures for this dictionary.""" #pylint: disable=W0105
    
    dt = dict
    """Exctraction nesting dictionary setting. This class will be used to create deep nesting structures when this object is extracted.""" #pylint: disable=W0105
    
    @property
    def dn(self):
        """Deep nesting attribute reader"""
        return self._dn
    
    @dn.setter
    def dn(self,new_type):
        """Deep nesting type setter."""
        if new_type != self._dn:
            self._dn = new_type
            self.renest()
    
    def __init__(self, *args, **kwargs):
        super(Configuration, self).__init__()
        self.log = logging.getLogger(__name__)
        if not len(self.log.handlers):
            self.log.addHandler(logging.NullHandler())
        self._store = dict(*args, **kwargs)
        self._filename = None
        self._strict = False
    
    name = "Configuration"
    """The name/type of this configuration."""
        
    @property
    def filename(self):
        """The filename which has been used to save/load this configuration most recently"""
        return self._filename
        
    def __repr__(self):
        """String representation of this object"""
        return repr(self.store)
        
    def __str__(self):
        """String for this object"""
        return "<%s %s >" % (self.name,repr(self))
        
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
    
    def update(self, other, deep=True): #pylint: disable=W0221
        """Update the dictionary using :meth:`merge`.
        
        :param dict-like other: The other dictionary to be merged.
        :param bool deep: Whether to use deep merge (:meth:`merge`) or shallow update.
        
        """
        if deep:
            self.merge(other)
        else:
            self._store.update(other)
    
    def merge(self, other):
        """Merge another configuration into this one (the master).
        
        :param dict-like other: The other dictionary to be merged.
        
        """
        deepmerge(self, other, self.dn)
    
    def save(self, filename, silent=True):
        """Save this configuration as a YAML file. YAML files generally have the ``.yaml`` or ``.yml`` extension. If the filename ends in ``.dat``, the configuration will be saved as a raw dictionary literal.
        
        :param string filename: The filename on which to save the configuration.
        :param bool silent: Unused.
        
        """
        if hasattr(filename,'read') and hasattr(filename,'readlines'):
            stream.write("# %s: stream" % self.name)
            yaml.dump(self.store, stream, default_flow_style=False)
        else:
            with open(filename, "w") as stream:
                stream.write("# %s: %s\n" % (self.name,filename))
                if re.search(r"(\.yaml|\.yml)$", filename):
                    yaml.dump(self.store, stream, default_flow_style=False, encoding='utf-8')
                elif re.search(r"\.dat$", filename):
                    stream.write(str(self.store))
                elif not silent:
                    raise ValueError("Filename Error, not (.dat,.yaml,.yml): %s" % filename)
                self._filename = filename
        
    def load(self, filename, silent=True):
        """Loads a configuration from a yaml file, and merges it into the master configuration.
        
        :param string filename: The filename to load from.
        :param bool silent: Silence IOErrors which might arise due to a non-existant configuration file. If this is the case, the failure to find a configuration file will be logged, will not raise an error.
        :raises IOError: if the file can't be found.
        :returns: boolean, whether the file was loaded.
        """
        loaded = False
        try:
            if hasattr(filename,'read') and hasattr(filename,'readlines'):
                new = yaml.load(filename)
            else:
                with open(filename, "r") as stream:
                    new = yaml.load(stream)
        except IOError:
            if silent:
                self.log.warning("Could not load configuration from file: %s" % filename)
            else:
                raise
        else:
            self.merge(new)
            self._filename = filename
            loaded = True
        return loaded
    
    @property
    def store(self):
        """Dictionary representing this configuration. This property should be used if you wish to have a 'true' dictionary object. It is used internally to write this configuration to a YAML file.
        """
        return reformat(self._store,self.dt)
    
    def renest(self, deep_nest_type=None):
        """Re-nest this object. This method applies the :attr:`dn` deep-nesting attribute to each nesting level in the configuration object.
        
        :param deep_nest_type: mapping nesting type, will set :attr:`dn`.
        
        This method does not return anything.
        """
        if isinstance(deep_nest_type, collections.Mapping):
            self._dn = deep_nest_type #pylint: disable=C0103
        elif deep_nest_type is not None:
            TypeError("%r is not a mapping type." % deep_nest_type)
        self._store = reformat(self._store,self.dn)
        
    def extract(self):
        """Extract the dictionary from this object.
        
        .. deprecated:: 0.4
            use :attr:`store`
        
        """
        return self.store
        
    def configure(self,module=__name__,defaultcfg=False,cfg=False,supercfg=None):
        """The configuration loads (starting with a blank configuration):
        
            1. The list of `supercfg`s. This list should contain tuples of \
            (module,name) pairs.
            2. The `module` configuration file named for `defaultcfg`
            3. The command line specified file from the user's home folder \
            ``~/config.yml``
            4. The command line specified file from the working directory.
        
        If the fourth file is not found, and the user specified a new name for \
        the configuration file, then the user is warned that no configuration \
        file could be found. This way the user is only warned about a missing \
        configuration file if they requested a file specifically (and so \
        intended to use a customized file).
        
        :param module: The name of the module for searching for the default config.
        :param cfg: The name of the requested configuration file.
        :param defaultcfg: The name of the default configuration file which might \
        exist in the module's file.
        :param: supercfg: A list of configuration files to preload. The list should \
        contian pairs of (module,name) as tuples.
        
        """
        from pkg_resources import resource_filename
        if not defaultcfg:
            return
        if supercfg is None:
            supercfg = []
        for supermodule,superfilename in supercfg:
            if supermodule == '__main__':
                self.load(superfilename)
            else:
                self.load(resource_filename(supermodule,superfilename))
        if module != '__main__':
            self.load(resource_filename(module,defaultcfg))
        if cfg and util.check_exists("~/%s" % cfg):
            self.load(os.path.expanduser("~/%s" % cfg))
        if cfg and os.path.exists(cfg):
            self.load(cfg, silent=False)
        elif cfg and cfg != defaultcfg:
            warn("Configuration File '{}' not found!".format(cfg), RuntimeWarning)
        
        
    @classmethod
    def create(cls,module=__name__,defaultcfg=False,cfg=False,supercfg=None):
        """Create a configuration from a series of YAML files.
        
        See :meth:`configure` for a detailed description of the resolution order of configuration files for this method.
        """
        config = cls()
        config.configure(module,defaultcfg,cfg,supercfg)
        return config


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
        
    def _getitem(self, store, parts):
        """Recursive getitem calling function."""
        key = parts.pop(0)
        if len(parts) == 0:
            if store.get(key) == self.dn() and self._strict:
                raise KeyError
            return store[key]
        elif not self._strict:
            store.setdefault(key, self.dn())
        return self._getitem(store[key], parts)
            
    def _setitem(self, store, parts, value=None):
        """Recursive setitem calling function
        
        This function handles a few things:
        - Store is passed in as a variable to make the recursive mode work.
        - If there are no more parts left, then we call the store's setitem.
        - If there are parts left, then we get the value of the next key in line. When we do this, if that key has not been set, we use a default nester, the ``self.dn`` attribute, which should construct a mapping object.
        - Recurses into the system."""
        key = parts.pop(0)
        if len(parts) == 0:
            return store.__setitem__(key, value)
        elif not self._strict:
            store.setdefault(key, self.dn())
        return self._setitem(store[key], parts, value)
            
    def _delitem(self, store, parts):
        """Recursive delitem calling function"""
        key = parts.pop(0)
        if len(parts) == 0:
            return store.__delitem__(key)
        elif not self._strict:
            store.setdefault(key, self.dn())
        return self._delitem(store[key], parts)
            
    def _contains(self, store, parts):
        """Recursive containment algorithm"""
        key = parts.pop(0)
        if len(parts) == 0:
            if ((isinstance(store.get(key),self.dn) 
                and not bool(store.get(key))) 
                and self._strict):
                return False
            return store.__contains__(key)
        elif key in store:
            return self._contains(store[key],parts)
        else:
            return False
        
        
    def __getitem__(self, key):
        """Dictionary getter"""
        keyparts = key.split(".")
        try:
            if len(keyparts) > 1:
                return self._getitem(self, keyparts)
            elif ((isinstance(self._store.get(key),self.dn) 
                    and not bool(self._store.get(key)))
                    and self._strict):
                    raise KeyError
            return self._store[key]
        except KeyError:
            raise KeyError('%s' % key)
        
    def __setitem__(self, key, value):
        """Dictonary setter"""
        keyparts = key.split(".")
        if len(keyparts) > 1:
            return self._setitem(self, keyparts, value)
        return self._store.__setitem__(key, value)
        
    def __delitem__(self, key):
        """Dictionary delete"""
        keyparts = key.split(".")
        if len(keyparts) > 1:
            return self._delitem(self, keyparts)        
        return self._store.__delitem__(key)
        
    def __contains__(self,key):
        """Dictionary in"""
        keyparts = key.split(".")
        if len(keyparts) > 1:
            return self._contains(self, keyparts)
        elif ((isinstance(self._store.get(key),self.dn) 
                and not bool(self._store.get(key)))
                and self._strict):
                return False
        else:
            return self._store.__contains__(key)
    


class StructuredConfiguration(DottedConfiguration):
    """A structured configuration with some basic defaults for AstroObject-type classes.
    
    This class does two things differently for configurations:
    
    1. Configurations are stored in a "Configurations" variable set. They can then be loaded by configuration key instead of filename, using the :meth:`setFile` method to set the filename, and then calling :meth:`load` or meth:`save` with no arguments.
    2. Configuration variables can be accessed and set with dot-qualified names. E.g.::
        
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
    
    DEFAULT_FILENAME = "--NOFILE--"
    
    def __init__(self,  *args, **kwargs):
        super(StructuredConfiguration, self).__init__(*args, **kwargs)
        self._files = self.dn()
        self._files["This"] = self.DEFAULT_FILENAME
        self._files["Loaded"] = []
        self._files["Configurations"] = self.dn()
        self.__set_on_load = False
        
    @property
    def _set_on_load(self):
        """True for default filenames"""
        if self._files["This"] == self.DEFAULT_FILENAME:
            self.__set_on_load = True
        return self.__set_on_load
    
    def setFile(self, filename=None, name=None): #pylint: disable=C0103
        """Depricated Method"""
        return self.set_file(filename, name)
    
    def set_file(self, filename=None, name=None):
        """Set the default/current configuration file for this configuration.
        
        The configuration file set by this method will be used next time :meth:`load` or :meth:`save` is called with no filename.
        
        :param string filename: The filename to load from.
        :param string name: The name key for the file.
        
        """
        if not filename:
            if not name:
                raise ValueError("Must provide name or filename")
            if name not in  self._files["Configurations"]:
                raise KeyError("Key %s does not represent a configuration file." % name)
        else:
            if not name:
                name = os.path.basename(filename)
        if name not in self._files["Configurations"]:
            self._files["Configurations"][name] = filename
        self._files["This"] = self._files["Configurations"][name]
    
    def save(self, filename=None, silent=True):
        """Save the configuration to a YAML file. If ``filename`` is not provided, the configuration will use the file set by :meth:`setFile`.
        
        :param string filename: Destination filename.
        
        Uses :meth:`Configuration.save`.
        """
        if filename == None:
            filename = self._files["This"]
        return super(StructuredConfiguration, self).save(filename)
    
        
    def load(self, filename=None, silent=True):
        """Load the configuration to a YAML file. If ``filename`` is not provided, the configuration will use the file set by :meth:`setFile`.
        
        :param string filename: Target filename.
        :param bool silent: Whether to raise an error if the target file cannot be found.
        
        Uses :meth:`Configuration.load`."""
        if filename == None:
            filename = self._files["This"]
        loaded = super(StructuredConfiguration, self).load(filename, silent)
        if loaded and self._set_on_load:
            self._files["Loaded"].append(filename)
