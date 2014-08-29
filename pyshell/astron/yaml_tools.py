# -*- coding: utf-8 -*-
# 
#  yaml.py
#  pyshell
#  
#  Created by Alexander Rudy on 2014-03-06.
#  Copyright 2014 University of California. All rights reserved.
# 

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)


"""
YAML tags for astropy.quantity objects
======================================
"""

def astropy_quantity_yaml_factory(astropy_type, Loader=None, Dumper=None, python_type=float):
    """Represent a quantity type"""
    
    tag = "!{}".format(astropy_type.__name__.lower())
    
    if Dumper is not None:
        def astropy_representer(dumper, data):
            return dumper.represent_scalar(tag, "{0.value} {0.unit:generic}".format(data))
        astropy_representer.__doc__ = "A {0} representer yielding the {1} tag.".format(astropy_type.__name__, tag)
        Dumper.add_representer(astropy_type, astropy_representer)
        
    if Loader is not None:
        def astropy_constructor(loader, node):
            scalar_value = loader.construct_scalar(node)
            parts = scalar_value.split(" ")
            value = parts[0]
            unit = " ".join(parts[1:])
            return astropy_type(python_type(value), unit=unit)
        astropy_constructor.__doc__ = "A {0} constructor interpreting the {1} tag.".format(astropy_type.__name__, tag)
        Loader.add_constructor(tag, astropy_constructor)
    
def astropy_direct_yaml_factory(astropy_type, Loader=None, Dumper=None):
    """Represent a quantity type"""
    
    tag = "!{}".format(astropy_type.__name__.lower())
    
    if Dumper is not None:
        def astropy_representer(dumper, data):
            return dumper.represent_scalar(tag, "{0.value} {0.unit:generic}".format(data))
        astropy_representer.__doc__ = "A {0} representer yielding the {1} tag.".format(astropy_type.__name__, tag)
        Dumper.add_representer(astropy_type, astropy_representer)
        
    if Loader is not None:
        def astropy_constructor(loader, node):
            scalar_value = loader.construct_scalar(node)
            return astropy_type(scalar_value)
        astropy_constructor.__doc__ = "A {0} constructor interpreting the {1} tag.".format(astropy_type.__name__, tag)
        Loader.add_constructor(tag, astropy_constructor)