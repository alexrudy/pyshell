# -*- coding: utf-8 -*-
# 
#  test_package.py
#  pyshell
#  
#  Created by Jaberwocky on 2013-04-12.
#  Copyright 2013 Jaberwocky. All rights reserved.
# 

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)

import shutil, os, os.path
import pyshell.subcommand
import nose.tools as nt
import warnings
from nose.plugins.skip import Skip,SkipTest
from subprocess import CalledProcessError, Popen, PIPE
import shlex
from .util import dests_from_argparse
from .test_base import test_base_cliengine

class test_subcommand_scengine(test_base_cliengine):
    """pyshell.subcommand.SCEngine"""
    
    BASE_CLASS = pyshell.subcommand.SCEngine
    
    def setup(self):
        """Fix DEFAULTCFG in SCEngine"""
        super(test_subcommand_scengine, self).setup()
        self.CLASS.defaultcfg = "Config.yml"

# class test_subcommand_sccontroller(test_base_cliengine):
#     """pyshell.subcommand.SCController"""
#     
#     CLASS = pyshell.subcommand.SCController

del test_base_cliengine
