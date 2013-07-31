# 
#  __init__.py
#  pyshell
#  
#  Created by Alexander Rudy on 2012-09-29.
#  Copyright 2012 Alexander Rudy. All rights reserved.
# 
"""
PyShell master module
=====================

Use this for quick access to commonly used classes!
"""

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)

# pylint: disable = invalid-name

version = "0.3.2"
__all__ = []

from .base import *
import base
__all__ += base.__all__

from loggers import getLogger, getSimpleLogger, configure_logging
__all__ += ['getLogger' , 'getSimpleLogger', 'configure_logging']

import loggers
loggers.buffer_logger()

from .subcommand import SCEngine, SCController
__all__ += ['SCEngine', 'SCController']