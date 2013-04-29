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
from pyshell import CLIEngine, PYSHELL_LOGGING_STREAM, PYSHELL_LOGGING_STREAM_ALL
from pyshell.util import ipydb
import pyshell.loggers
import os, warnings, logging

logging.captureWarnings(True)
slog = pyshell.loggers.getSimpleLogger("a.b.c.d")
slogb = pyshell.loggers.getSimpleLogger("a.b")
slog.info("slog INFO")
slogb.status("slogb STATUS")
log = pyshell.loggers.getLogger()
mlog = pyshell.loggers.getLogger(__name__)


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
        warnings.warn("This is a warnings.warn!")
        
    def do(self):
        """Take the actual action"""
        self.log.debug(".do DEBUG")
        self.log.info(".do INFO")
        self.log.warn(".do WARN")
        self.log.critical(".do CRITICAL")
        self.log.status(".do STATUS")
        log.info(".do root INFO")
        mlog.info(".do __main__ INFO")
        mlog.status(".do __main__ STATUS")
        slog.status(".do a.b.c.d. STAUTS")
                
        
if __name__ == '__main__':
    LoggerExample.script()
    