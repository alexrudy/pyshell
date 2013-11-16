# -*- coding: utf-8 -*-
# 
#  yaml.py
#  pyshell
#  
#  Created by Jaberwocky on 2013-11-15.
#  Copyright 2013 Jaberwocky. All rights reserved.
# 
"""

.. _loaders:

:mod:`yaml` compatible Loaders
------------------------------

The loader interface provides |Loader| objects which can be used directly::
    
    yaml.load(stream, Loader=UnicodeLoader)
    
These loaders use the mixin interface described in :ref:`mixin`. Loader objects implement the entirety of
the YAML parsing engine, so customization of any of the YAML base classes can be done via loaders.

.. autoclass:: OrderedDictLoader

.. autoclass:: OrderedDictSafeLoader

.. autoclass:: UnicodeLoader

.. autoclass:: UnicodeSafeLoader

.. autoclass:: PyshellLoader

.. inheritance-diagram::
    OrderedDictLoader
    OrderedDictSafeLoader
    UnicodeLoader
    UnicodeSafeLoader
    PyshellLoader

.. _dumpers:

:mod:`yaml` compatible Dumpers
------------------------------

The dumper interface provides |Dumper| objects which can be used directly::
    
    yaml.dump(data, stream, Dumper=UnicodeLoader)
    
These dumpers use the mixin interface described in :ref:`mixin`. Dumper objects implement the entirety of
the YAML parsing engine, so customization of any of the YAML base classes can be done via dumpers.

.. autoclass:: OrderedDictDumper

.. autoclass:: OrderedDictSafeDumper

.. autoclass:: UnicodeDumper

.. autoclass:: UnicodeSafeDumper

.. autoclass:: MappingDumper

.. autoclass:: MappingSafeDumper

.. autoclass:: PyshellDumper

.. inheritance-diagram::
    OrderedDictDumper
    OrderedDictSafeDumper
    MappingDumper
    MappingSafeDumper
    PyshellDumper

.. _mixin:

Mixin Interface
---------------

The Mixin Interface provides classes which can be used with the default :mod:`yaml`
loaders and dumpers to create new loaders and dumpers with modified behavior. You
should always ensure to inherit from the :mod:`yaml` loaders and dumpers last, to ensure
that the required methods are overwritten by the mixins here. 

Many mixins will work without providing any subclass content. 
For example, to make a unicode-compatible loader, you might use::
    
    class MyUnicodeLoader(UnicodeYAMLLoader, yaml.SafeLoader):
        pass
    

In fact, this is how this module defines the :class:`UnicodeSafeLoader`.

Mixins for Loaders
******************

.. autoclass::
    UnicodeYAMLLoader
    
.. autoclass::
    MappingYAMLLoader


Mixins for Dumpers
******************

.. autoclass::
    UnicodeYAMLDumper
    
.. autoclass::
    ClassMappingYAMLDumper


.. _functions:

Function Interface
------------------

The functional interface provides three functions which implement
the functionality found in the rest of the class through a functional
interface. The only functionality not implemented is the mapping loader
:class:`MappingYAMLLoader`.

By default, the functions below take no arguments, and then apply their
modifications to |Loader|, |SafeLoader| and |Dumper|.

Functions for Loaders
*********************

.. autofunction::
    load_yaml_unicode

Functions for Dumpers
*********************

.. autofunction::
    dump_yaml_unicode
    
.. autofunction::
    dump_yaml_subclasses
    
.. autofunction::
    dump_yaml_classmapping

.. |odict| replace:: :class:`~collections.OrderedDict`
.. |Dumper| replace:: :class:`yaml.Dumper`
.. |Loader| replace:: :class:`yaml.Loader`
.. |SafeDumper| replace:: :class:`yaml.SafeDumper`
.. |SafeLoader| replace:: :class:`yaml.SafeLodaer`

"""

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)
                        
import yaml
import six
import abc
from collections import OrderedDict, Mapping

__all__ = ['load_yaml_unicode', 'dump_yaml_unicode'
            'dump_yaml_subclasses', 'dump_yaml_classmapping'
            'OrderedDictLoader', 'OrderedDictSafeLoader',
            'OrderedDictDumper', 'OrderedDictSafeDumper',
            'MappingDumper', 'MappingSafeDumper',
            'UnicodeLoader', 'UnicodeSafeLoader',
            'UnicodeDumper', 'UnicodeSafeDumper'
            'PyshellLoader', 'PyshellDumper'
            'MappingYAMLLoader', 'UnicodeYAMLLoader']

YAML_LOADERS = [yaml.Loader, yaml.SafeLoader]
YAML_DUMPERS = [yaml.SafeDumper]
    
def dump_yaml_subclasses(subclass, representclass, *dumpers):
    """Dump an ordered dict like you would a regular dict."""
    if not len(dumpers):
        dumpers = YAML_DUMPERS
    for dumper in dumpers:
        dumper.add_multi_representer(subclass, dumper.yaml_representers[representclass])
    
def dump_yaml_classmapping(fromclass, toclass, *dumpers):
    """Map one class to another in the YAML representer."""
    if not len(dumpers):
        dumpers = YAML_DUMPERS
    for dumper in dumpers:
        dumper.add_representer(fromclass, dumper.yaml_representers[toclass])

def load_yaml_unicode(*loaders):
    """This method forces the PyYAML library to construct unicode objects when
    reading YAML instead of producing regular strings.
    
    It is designed to improve compatibility in Python2.x using unicode 
    objects.
    """
    
    def construct_yaml_str(self, node):
        """Constructs a regular scalar instead of a python
        string object from a YAML key, forcing all YAML strings
        to be unicode objects."""
        return self.construct_scalar(node)
    
    if not len(loaders):
        loaders = YAML_LOADERS
    
    for loader in loaders:
        loader.add_constructor('tag:yaml.org,2002:str', construct_yaml_str)
    
def dump_yaml_unicode(*dumpers):
    """This method forces the PyYAML library to dump unicode objects when
    dumping YAML instead of producing YAML unicode tags."""
    if not len(dumpers):
        dumpers = YAML_DUMPERS
    
    def represent_unicode(self, data):
        return self.represent_scalar('tag:yaml.org,2002:str', data)
    
    for dumper in dumpers:
        dumper.add_representer(six.text_type, represent_unicode)

@six.add_metaclass(abc.ABCMeta)
class UnicodeYAMLLoader(object):
    """
    A YAML loader that loads unicode values everywhere.
    
    This MixIn can be used for SafeLoaders and Regular Loaders. It doesn't work alone.
    """
    def __init__(self, *args, **kwargs):
        super(UnicodeYAMLLoader, self).__init__(*args, **kwargs)
        
        self.add_constructor('tag:yaml.org,2002:str', type(self).construct_yaml_str_unicode)
        
    def construct_yaml_str_unicode(self, node):
        """Constructs a regular scalar instead of a python
        string object from a YAML key, forcing all YAML strings
        to be unicode objects."""
        return self.construct_scalar(node)
    
class UnicodeYAMLDumper(object):
    """This Mixin can be used for |Dumper| and |SafeDumper| to provide unicode loading support
    by default."""
    def __init__(self, *args, **kwargs):
        super(UnicodeYAMLDumper, self).__init__(*args, **kwargs)
        
        self.add_representer(six.text_type, type(self).represent_unicode)
    
    def represent_unicode(self, data):
        return self.represent_scalar('tag:yaml.org,2002:str', data)

@six.add_metaclass(abc.ABCMeta)
class MappingYAMLLoader(object):
    """
    A YAML loader that loads mappings into ordered dictionaries.
    
    This MixIn can be used for SafeLoaders and Regular Loaders. It doesn't work alone.
    
    It has an abstract attribute, :attr:`CUSTOM_MAPPING` which must be set to the desired
    mapping type in a subclass before use.
    
    Original Design From: https://gist.github.com/enaeseth/844388
    """
    
    @abc.abstractproperty
    def CUSTOM_MAPPING(self):
        """set this attribute to the desired custom mapping."""
        pass
    
    def __init__(self, *args, **kwargs):
        super(MappingYAMLLoader, self).__init__(*args, **kwargs)

        self.add_constructor('tag:yaml.org,2002:map', type(self).construct_yaml_map)
        self.add_constructor('tag:yaml.org,2002:omap', type(self).construct_yaml_map)

    def construct_yaml_map(self, node):
        data = self.CUSTOM_MAPPING()
        yield data
        value = self.construct_mapping(node)
        data.update(value)

    def construct_mapping(self, node, deep=False):
        if isinstance(node, yaml.MappingNode):
            self.flatten_mapping(node)
        else:
            raise yaml.constructor.ConstructorError(None, None,
                'expected a mapping node, but found %s' % node.id, node.start_mark)

        mapping = self.CUSTOM_MAPPING()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError as exc:
                raise yaml.constructor.ConstructorError('while constructing a mapping',
                    node.start_mark, 'found unacceptable key (%s)' % exc, key_node.start_mark)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping
        
@six.add_metaclass(abc.ABCMeta)
class ClassMappingYAMLDumper(object):
    """A Mixin for YAML Mapping."""
    
    @abc.abstractproperty
    def CUSTOM_CLASSMAPPING(self):
        """set this attribute to the desired custom mapping."""
        pass
        
    @abc.abstractproperty
    def CUSTOM_SUBCLASSMAPPING(self):
        """set this attribute to the desired custom mapping."""
        pass
    
    def __init__(self, *args, **kwargs):
        super(ClassMappingYAMLDumper, self).__init__(*args, **kwargs)
        
        for fromclass, toclass in self.CUSTOM_CLASSMAPPING.items():
            self.add_representer(fromclass, type(self).yaml_representers[toclass])
        
        for subclass, toclass in self.CUSTOM_SUBCLASSMAPPING.items():
            self.add_multi_representer(subclass, type(self).yaml_representers[toclass])
        
# OrderedDict Loaders
#####################

class OrderedDictLoader(MappingYAMLLoader, yaml.Loader):
    """A |Loader| which uses |odict| instead of regular dictionaries."""
    CUSTOM_MAPPING = OrderedDict
    
class OrderedDictSafeLoader(MappingYAMLLoader, yaml.SafeLoader):
    """A |SafeLoader| which uses |odict| instead of regular dictionaries."""
    CUSTOM_MAPPING = OrderedDict
    
    

# Unicode Loaders
#################

class UnicodeLoader(UnicodeYAMLLoader, yaml.Loader):
    """A |Loader| which uses unicode for all keys and strings."""
    pass

class UnicodeSafeLoader(UnicodeYAMLLoader, yaml.SafeLoader):
    """A |SafeLoader| which uses unicode for all keys and strings."""
    pass

# PyShell Loaders combine Unicode and OrderedDict Loaders
#########################################################

class PyshellLoader(MappingYAMLLoader, UnicodeYAMLLoader, yaml.SafeLoader):
    """A |Loader| which uses unicode by default and |odict|."""
    CUSTOM_MAPPING = OrderedDict
    
class PyshellDumper(ClassMappingYAMLDumper, UnicodeYAMLDumper, yaml.SafeDumper):
    """A |SafeDumper| which uses unicode by default and |odict|."""
    CUSTOM_CLASSMAPPING = {}
    CUSTOM_SUBCLASSMAPPING = { dict: dict }

# OrderedDict Dumpers
#####################

class OrderedDictDumper(ClassMappingYAMLDumper, yaml.Dumper):
    """A |Dumper| which dumps |odict| as a regular :class:`dict`."""
    CUSTOM_CLASSMAPPING = { OrderedDict : dict }
    CUSTOM_SUBCLASSMAPPING = {}
    
class OrderedDictSafeDumper(ClassMappingYAMLDumper, yaml.SafeDumper):
    """A |SafeDumper| which dumps |odict| as a regular :class:`dict`."""
    CUSTOM_CLASSMAPPING = { OrderedDict : dict }
    CUSTOM_SUBCLASSMAPPING = {}
    

# Unicode Dumpers
#################

class UnicodeDumper(UnicodeYAMLDumper, yaml.Dumper):
    """A |Dumper| that dumps all keys and strings as unicode literals."""
    pass

class UnicodeSafeDumper(UnicodeYAMLDumper, yaml.SafeDumper):
    """A |SafeDumper| that dumps all keys and strings as unicode literals."""
    pass

# Mapping Dumpers
#################

class MappingDumper(ClassMappingYAMLDumper, yaml.Dumper):
    """A |Dumper| which dumps any mapping as regular mappings."""
    CUSTOM_CLASSMAPPING = {}
    CUSTOM_SUBCLASSMAPPING = { dict: dict, Mapping: dict}

class MappingSafeDumper(ClassMappingYAMLDumper, yaml.SafeDumper):
    """A |SafeDumper| which dumps any mapping as regular mappings."""
    CUSTOM_CLASSMAPPING = {}
    CUSTOM_SUBCLASSMAPPING = { dict: dict, Mapping: dict }
    
