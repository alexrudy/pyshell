# -*- coding: utf-8 -*-
# 
#  util.py
#  tests
#  
#  Created by Jaberwocky on 2013-04-01.
#  Copyright 2013 Jaberwocky. All rights reserved.
# 

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)


import argparse
import os

def dests_from_argparse(parser):
    """Get destinations from a parser"""
    return [ action.dest for action in parser._actions ]

def on_travis_ci():
    """Check whether we are on travis"""
    return os.environ.get("CI",False) and os.environ.get("TRAVIS",False)