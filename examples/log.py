#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
#  hello.py
#  pyshell
#  
#  Created by Jaberwocky on 2013-03-15.
#  Copyright 2013 Jaberwocky. All rights reserved.
# 
"""
This is a basic usage example for CLIEngine.
"""
from __future__ import print_function, unicode_literals
from pyshell import CLIEngine, PYSHELL_LOGGING_STREAM
from pyshell.util import ipydb
import os

ipydb()

class LoggerExample(CLIEngine):
    """Say hello in English, French, or another language."""
    
    supercfg = PYSHELL_LOGGING_STREAM
    
    defaultcfg = "hello.yml"
    
    description = "Test Loggers!"
    
    def init(self):
        """Arguments to be set up at the beginning. By default, this function will set up the --config argument."""
        super(LoggerExample, self).init()
        self.log.info(".init INFO")
        self.log.debug(".init DEBUG")
        
    def configure(self):
        """Configure the engine for operation, before help will be printed."""
        super(LoggerExample, self).configure()
        self.log.warn(".configure WARN")

    def parse(self):
        """Do any parsing"""
        super(LoggerExample, self).parse()
        self.log.critical(".parse CRITICAL")
        
    def do(self):
        """Take the actual action"""
        self.log.debug(".do DEBUG")
        self.log.info(".do INFO")
        self.log.warn(".do WARN")
        self.log.critical(".do CRITICAL")
        self.log.log(25,".do STATUS")
        
        
if __name__ == '__main__':
    LoggerExample.script()
    