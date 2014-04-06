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

version = "0.6.2"
__all__ = []

from .base import *
__all__ += ['CLIEngine',
    'PYSHELL_LOGGING','PYSHELL_LOGGING_STREAM','PYSHELL_LOGGING_STREAM_ALL']

from .loggers import getLogger, getSimpleLogger, configure_logging, buffer_logger
__all__ += ['getLogger' , 'getSimpleLogger', 'configure_logging']
buffer_logger()
del buffer_logger # Cleanup Namespace

from .subcommand import SCEngine, SCController
__all__ += ['SCEngine', 'SCController']