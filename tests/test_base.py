# -*- coding: utf-8 -*-
# 
#  test_base.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-01-12.
#  Copyright 2013 Alexander Rudy. All rights reserved.
# 

import shutil, os, os.path
import pyshell.base
import nose.tools as nt
import warnings
from nose.plugins.skip import Skip,SkipTest
from subprocess import CalledProcessError, Popen, PIPE

class test_base_cliengine(object):
    """pyshell.base.CLIEngine"""
    
    def setup(self):
        self.CLASS = pyshell.base.CLIEngine
        
    @nt.raises(TypeError)
    def test_base_init(self):
        """__init__"""
        self.CLASS()
        
    