# -*- coding: utf-8 -*-
# 
#  bump_version.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-01-12.
#  Copyright 2013 Alexander Rudy. All rights reserved.
# 
from __future__ import division
"""
bump_version -- Increase version numbers!
"""
from .base import CLIEngine

class VersionBumper(CLIEngine):
    """Bump the version of your source code!"""
    def __init__(self, arg):
        super(VersionBumper, self).__init__()
        self.arg = arg
        