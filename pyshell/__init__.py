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

from .base import *
import base
from .subcommand import SCEngine, SCController
__all__ = ['SCEngine', 'SCController'] + base.__all__