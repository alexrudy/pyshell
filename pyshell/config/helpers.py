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
    def __init__(self, config, **kwargs):
        self.config = config
        if kwargs.get('dest',None) in self.config:
            kwargs.setdefault('default', self.config[kwargs['dest']])
        super(ConfigureAction, self).__init__(**kwargs)
        
    def __call__(self, parser, namespace, values, option_string):
        """Parse this action. The value is applied to both the namespace and the configuration."""
        self.config[self.dest] = values
        setattr(namespace, self.dest, values)
        
        
class BoundConfigureAction(ConfigureAction):
    """A configure action which is bound."""
    def __init__(self, config=None, **kwargs):
        if config is not None:
            raise ValueError("Cannot pass a configuration instance to a bound configuration action.")
        super(BoundConfigureAction, self).__init__(config=self.config,**kwargs)
        
def bind_configuration_action(configuration):
    """Return a bound configuration item."""
    class _BoundConfigureAction(BoundConfigureAction):
        config = configuration
    return _BoundConfigureAction
        
        
class ConfigurationProperty(TypedProperty):
    """A configuration item property."""
    def __init__(self, configuration_type=Configuration):
        if not issubclass(configuration_type, Configuration):
            raise ValueError("{} must use a subclass of {} as the configuration type. Got {}".format(self,
            Configuration, configuration_type))
        super(ConfigurationProperty, self).__init__("configuration", Configuration, readonly=True, init_func=configuration_type)

class ConfigurationItemProperty(object):
    """A property which accessess an underlying configuration item"""
    def __init__(self, configvalue, configattr='config', readonly=False, postget=lambda x : x, preset=lambda x : x):
        super(ConfigurationItemProperty, self).__init__()
        self.configvalue = configvalue
        self.configattr = configattr
        self.readonly = readonly
        self.postget = postget
        self.preset = preset
        
    @descriptor__get__
    def __get__(self, obj, objtype):
        """Descriptor get."""
        config = getattr(obj, self.configattr)
        return self.postget(config[self.configvalue])
        
    def __set__(self, obj, value):
        """Descriptor set."""
        if self.readonly:
            raise AttributeError("Cannot set a read-only configuration attribute.")
        else:
            config[self.configvalue] = self.preset(value)
        