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

# pylint: disable = invalid-name

version = "0.2.0"
__all__ = []

from .base import *
import base
__all__ += base.__all__

from loggers import getLogger, getSimpleLogger
__all__ += ['getLogger' , 'getSimpleLogger']

import loggers
loggers.buffer_logger()

from .subcommand import SCEngine, SCController
__all__ += ['SCEngine', 'SCController']