# -*- coding: utf-8 -*-
# 
#  loggers.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-04-26.
#  Copyright 2013 Alexander Rudy. All rights reserved.
# 
from __future__ import (absolute_import, unicode_literals, division,
                        print_function)

import logging, logging.config
import logging.handlers as handlers

import math
import copy
import sys
import time
import os
import yaml
import collections

from .console import get_color

__all__ = ['configure_logging','debuffer_logger','GrowlHandler',
    'ManyTargetHandler','BufferHandler','getLogger','buffer_root','status']

def configure_logging(configuration):
    """Setup logging from a configuration object."""
    from .config import DottedConfiguration
    if isinstance(configuration,DottedConfiguration):
        config = configuration
    elif isinstance(configuration,collections.Mapping):
        config = DottedConfiguration(configuration)
    elif isinstance(configuration,tuple):
        config = DottedConfiguration.fromresource(*configuration)
    elif isinstance(configuration,basestring):
        config = DottedConfiguration.fromfile(configuration)
    
    if "logging" in config:
        for logger in config["logging.loggers"]:
            _prepare_config(logger)
        if "root" in config["logging"]:
            _prepare_config()
        logging.config.dictConfig(config["logging"])
        if "py.warnings" in config["logging.loggers"]:
            logging.captureWarnings(True)
        for logger in config["logging.loggers"]:
            debuffer_logger(logger)
        if "root" in config["logging"]:
            debuffer_logger()
    

def status(log,*args,**kwargs):
    """Log status!"""
    log.log(25,*args,**kwargs)
    
def getLogger(name=None):
    """Return a logger with the buffered handler attached."""
    logger = logging.getLogger(name)
    if not len(logger.handlers):
        logger.addHandler(BufferHandler(1e7))
        logger.status = status
    return logger

_buffers = {}
def _prepare_config(name=None):
    """docstring for prepare_config"""
    if name is not None:
        logger = logging.getLogger(name)
    else:
        logger = logging.getLogger()
        name = "__root__"
    debuffer = False
    for handler in logger.handlers:
        if isinstance(handler,BufferHandler):
            debuffer = handler
            break
    _buffers[name] = debuffer
    
    
def debuffer_logger(name=None):
    """Debuffer a given logger"""
    if name is not None:
        logger = logging.getLogger(name)
    else:
        name = "__root__"
        logger = logging.getLogger()
    debuffer = _buffers.get(name,False)
    if not debuffer:
        for handler in logger.handlers:
            if isinstance(handler,BufferHandler):
                debuffer = handler
                break
    if not debuffer:
        return
    
    for handler in logger.handlers:
        if not isinstance(handler,BufferHandler):
            debuffer.setTarget(handler)
    debuffer.close()
    logger.removeHandler(debuffer)
    
    

class GrowlHandler(logging.Handler):
    """Handler that emits growl notifications using the gntp module.
    
    Growl notifications are displayed by the growl framework application on desktop computers. They can also be sent over a network to notify a remote host. This logger turns log messages into growl notifications."""
    def __init__(self,name=None):
        super(GrowlHandler, self).__init__()
        self.name = name
        if self.name == None:
            self.name = sys.argv[0]
        try:
            import gntp
            import gntp.notifier
            self.gntp = gntp
        except ImportError as e:
            self.disable = True
            self.notifier = None
        else:
            self.disable = False
            self.notifier = self.gntp.notifier.GrowlNotifier(
                applicationName=self.name,
                notifications=self.mapping.values(),
                defaultNotifications=[ v for k,v in self.mapping.items() if k >= logging.INFO ],
            )
            self.notifier.register()
        self.titles = {
            logging.DEBUG:"%s Debug" % self.name,
            logging.INFO:"%s Info" % self.name,
            logging.WARNING:"%s Warning" % self.name,
            logging.CRITICAL:"%s Critical" % self.name,
            logging.ERROR:"%s Error" % self.name,
            }
        
    
    mapping = {logging.DEBUG:"Debug Message",logging.INFO:"Info Message",logging.WARNING:"Warning Message",logging.CRITICAL:"Critical Message",logging.ERROR:"Error Message"}

    
    
    def emit(self,record):
        """Emits a growl notification"""
        if self.disable:
            return
        try:
            msg = self.format(record)
            self.notifier.notify(
                noteType = self.mapping.get(record.levelno,self.mapping[logging.DEBUG]),
                title = self.titles.get(record.levelno,self.titles[logging.DEBUG]),
                description = msg,
                sticky = False,
                priority = 1,
            )
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
            
class ColorStreamFormatter(logging.Formatter):
    """Print to stream with colors!"""
    
    color = {
        logging.DEBUG : "magenta",
        logging.INFO : "green",
        logging.WARN : "yellow",
        logging.ERROR : "red",
    }
    
    def format(self, record):
        """Format a record with colors from the terminal module."""
        if record.levelno <= logging.DEBUG:
            record.color = ""
        elif record.levelno < logging.INFO:
            record.color = get_color(self.color[logging.DEBUG])
        elif record.levelno < logging.WARN:
            record.color = get_color(self.color[logging.INFO])
        elif record.levelno < logging.ERROR:
            record.color = get_color(self.color[logging.WARN])
        else:
            record.color = get_color(self.color[logging.ERROR])
        
        if record.color == "":
            record.nocolor = ""
        else:
            record.nocolor = get_color("Normal")
            
        return super(ColorStreamFormatter, self).format(record)
        
        
class ManyTargetHandler(handlers.MemoryHandler):
    """A new default handler (similar to a NULL handler) which holds onto targets for later."""
    def __init__(self, capacity, flushLevel=logging.ERROR, target=None, targets=None):
        super(ManyTargetHandler, self).__init__(capacity, flushLevel, target)
        if isinstance(self.target,logging.Handler):
            self.targets = set([self.target])
        else:
            self.targets = set()
        if isinstance(targets,collections.Sequence):
            self.targets += set(targets)

    def setTarget(self,target):
        """Add another target to the handler"""
        if isinstance(target,logging.Handler):
            self.targets.add(target)
                
    def flush(self):
        """Flush out this handler"""
        if len(self.targets) > 0:
            for record in self.buffer:
                for target in self.targets:
                    if (record.levelno >= target.level and
                        logging.getLogger(record.name).isEnabledFor(record.levelno)):
                        target.handle(record)
            self.buffer = []
    
    def close(self):
        """Close the handler"""
        super(ManyTargetHandler, self).close()
        self.targets = set()
        
        
class BufferHandler(ManyTargetHandler):
    """A special case of ManyTargetHandler for use with :func:`debuffer_logger`."""
    
    level = 1
    
def buffer_root():
    """Buffer Root Loggers"""
    root_log = logging.getLogger()
    root_log.setLevel(1)
    root_log.addHandler(BufferHandler(1e7))
    
logging.addLevelName(25,'STATUS')
    
        