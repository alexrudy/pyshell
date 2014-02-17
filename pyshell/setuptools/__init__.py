# -*- coding: utf-8 -*-
# 
#  __init__.py
#  pyshell
#  
#  Created by Alexander Rudy on 2014-02-16.
#  Copyright 2014 Alexander Rudy. All rights reserved.
# 

__all__ = ['fix']

from .fix_console_scripts import monkey_patch_setuptools

def fix():
    """Fix the setuptools"""
    monkey_patch_setuptools()