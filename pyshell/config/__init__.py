# -*- coding: utf-8 -*-
# 
#  __init__.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-12-02.
#  Copyright 2013 Alexander Rudy. All rights reserved.
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

Argparse Action for Configurations: :class:`ConfigureAction`
------------------------------------------------------------

.. autoclass::
    pyshell.config.helpers.ConfigureAction
    

Descriptors for Configurations
------------------------------

.. autoclass::
    pyshell.config.helpers.ConfigurationProperty
    
.. autoclass::
    pyshell.config.helpers.ConfigurationItemProperty


"""

from .core import *
from . import core
__all__ = core.__all__
del core