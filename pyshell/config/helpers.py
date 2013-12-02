# -*- coding: utf-8 -*-
# 
#  helpers.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-12-02.
#  Copyright 2013 Alexander Rudy. All rights reserved.
# 

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)

import six
import argparse

from .core import Configuration
from ..util import TypedProperty, descriptor__get__

class ConfigureAction(argparse.Action):
    """An argument parser action for use with a configuration.
    
    This action applies an argparse argument to a configuration destination. The `dest`
    keyword is used as the destination key.
    
    :keyword config: The configuration to be updated.
    :keyword dest: The destination key in the configuration.
    :keyword default: The default configuration value.
    
    This action class can be passed as the ``action=`` keyword in :meth:`argparse.ArgumentParser.add_argument`.
    """
    def __init__(self, config=None, **kwargs):
        self.config = config
        if kwargs.get('dest',None) in self.config:
            kwargs.setdefault('default', self.config[kwargs['dest']])
        super(ConfigureAction, self).__init__(**kwargs)
        
    def __call__(self, parser, namespace, values, option_string):
        """Parse this action. The value is applied to both the namespace and the configuration."""
        self.config[self.dest] = values
        setattr(namespace, self.dest, values)
        
        
class ConfigurationProperty(TypedProperty):
    """A configuration item property."""
    def __init__(self):
        super(ConfigurationProperty, self).__init__("configuration", Configuration, readonly=True)

class ConfigurationItemProperty(object):
    """A property which accessess an underlying configuration item"""
    def __init__(self, configvalue, configattr='config'):
        super(ConfigurationItemProperty, self).__init__()
        self.configvalue = configvalue
        self.configattr = configattr
        
    @descriptor__get__
    def __get__(self, obj, objtype):
        """Descriptor get."""
        config = getattr(obj, self.configattr)
        return config[self.configvalue]
        
    def __set__(self, obj, value):
        """Descriptor set."""
        raise AttributeError("Cannot set a read-only configuration attribute.")
        