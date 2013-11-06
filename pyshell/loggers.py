# -*- coding: utf-8 -*-
# 
#  loggers.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-04-26.
#  Copyright 2013 Alexander Rudy. All rights reserved.
#
"""
:mod:`loggers` - Logging made Easy
==================================

This module complements the python :mod:`logging` module. It is designed to seamlessly integrate with other logging libraries. Behind the scenes, :mod:`loggers` adds buffering handlers to each new logger it creates, to allow for logging before the logging interface is configured. For simple logging scripts, try :func:`getSimpleLogger`.

Logger Functions
----------------

.. autofunction::
    configure_logging
    
.. autofunction::
    getLogger

.. autofunction::
    getSimpleLogger
        
.. autofunction::
    debuffer_logger
    
.. autofunction::
    buffer_logger
    

.. autoclass::
    ManyTargetHandler
    :members:

.. autoclass::
    BufferHandler
    :members:
    
.. autoclass::
    ColorStreamFormatter
    :members:

"""
from __future__ import (absolute_import, unicode_literals, division,
                        print_function)

import logging, logging.config
import logging.handlers as handlers

import math
import copy
import sys
import time
import os, os.path
import yaml
import collections


import warnings

from .console import get_color

__all__ = ['configure_logging','debuffer_logger','GrowlHandler',
    'ManyTargetHandler','BufferHandler','getLogger','buffer_root','status',
    'getSimpleLogger',
    'PYSHELL_LOGGING','PYSHELL_LOGGING_STREAM','PYSHELL_LOGGING_STREAM_ALL']

PYSHELL_LOGGING = [('pyshell','logging.yml')]
"""This constant item can be added to the superconfiguration 
:attr:`supercfg` to enable a default logging configuration setup. It should
probably be added first, so that your own code will override it."""

PYSHELL_LOGGING_STREAM = [('pyshell','logging-stream-only.yml')]
"""This constant item can be added to the superconfiguration 
:attr:`supercfg` to enable a default logging configuration setup. It 
should probably be added first, so that your own code will override it. 
It only provides stream loggers, not file handlers."""

PYSHELL_LOGGING_STREAM_ALL = [('pyshell','logging-stream-all.yml')]
"""This constant item can be added to the superconfiguration
:attr:`supercfg` to enable a default logging configuration setup. It 
should probably be added first, so that your own code will override it. 
It only provides stream loggers, not file handlers. Its logger is just a 
root logger at the lowest level!"""

def configure_logging(configuration):
    """Setup logging from a configuration object. Configuration should meet Python's :mod:`logging.config` configuration
    requirements. This method uses :func:`logging.config.dictConfig` to process configurations.
    
    :param configuration: Any object which can be interpreted by :meth:`pyshell.config.DottedConfiguration.make`.
    
    The loggers will be configured. If any loggers to be configured have a :class:`~loggers.BufferHandler`, that buffer
    will be emptied into the newly configured handlers.
    
    """ 
    from .config import DottedConfiguration
    config = DottedConfiguration.make(configuration)
    
    if "logging" in config:
        
        for logger in config["logging.loggers"]:
            _prepare_config(logger)
        if "root" in config["logging"]:
            _prepare_config()
        
        logging.config.dictConfig(config["logging"].store)
        
        if "py.warnings" in config["logging.loggers"]:
            captureWarnings(True)
        for logger in config["logging.loggers"]:
            debuffer_logger(logger)
        if "root" in config["logging"]:
            debuffer_logger()
    
def getLogger(name=None):
    """Return a logger for a specified name.
    
    This differs from the built-in :func:`logging.getLogger` function
    as it ensures that returned loggers will have a :class:`BufferHandler`
    attached if no other handlers are found. It can be otherwise used in place
    of :func:`logging.getLogger`."""
    logger = logging.getLogger(name)
    if not len(logger.handlers):
        logger.addHandler(BufferHandler(1e7))
    return logger
    

_simpleConfig = None
def _getSimpleConfig():
    """Retrieve the _SimpleConfig object, populating it if it doesn't exist."""
    from .config import DottedConfiguration
    global _simpleConfig
    if _simpleConfig is None:
        _simpleConfig = DottedConfiguration.fromresource('pyshell','logging-stream-all.yml')

def getSimpleLogger(name=None,level=None):
    """Retrieves a logger with a simple logging configuration setup,
    which writes colorful logging output to the console using the configuration
    provided by ``logging-stream-all.yml``. Only the root logger is configured with
    the console handler, all others have only a level set.
    
    :param name: The logger name to be returned (like in :func:`getLogger`).
    :param level: The level of the configured logger.
    
    Configurations are cumulative, so :func:`getSimpleLogger` can be called multiple times."""
    _simpleConfig = _getSimpleConfig()
    logger = getLogger(name)
    if level is not None and name is not None:
        _simpleConfig["logging.loggers."+name+".level"] = level
    elif level is not None:
        _simpleConfig["logging.root.level"] = level
    configure_logging(_simpleConfig)
    return logger
    
def activateSimpleLogging(ltype='simple'):
    """Activate simple logging using a logging configuration built in to PyShell."""
    _configurations = {
        'all' : PYSHELL_LOGGING_STREAM_ALL,
        'stream' : PYSHELL_LOGGING_STREAM,
        'basic' : PYSHELL_LOGGING,
        'simple' : _getSimpleConfig(),
    }
    if ltype not in _configurations:
        raise ValueError("Logging Type must be in {!r}".format(_configurations.keys()))
    configure_logging(_configurations[ltype])

_buffers = {}
def _prepare_config(name=None):
    """Prepare for configuration by saving the buffers for this logger.
    
    :param name: Name of the logger to prep for configuration.
    
    """
    logger = logging.getLogger(name)
    name = "__root__" if name is None else name
    debuffer = False
    for handler in logger.handlers:
        if isinstance(handler,BufferHandler):
            debuffer = handler
            break
    _buffers[name] = debuffer
    
def buffer_logger(name=None):
    """Buffer named logger.

    :param name: The name of the logger to buffer.

    This method will add a :class:`BufferHandler` to the
    named logger, and will remove the other handlers.
    """
    _log = logging.getLogger(name)
    _buffer = False
    for handler in _log.handlers[:]:
        if isinstance(handler,BufferHandler):
            _buffer = handler
        _log.removeHandler(handler)
    _log.setLevel(1)
    if not _buffer:
        _buffer = BufferHandler(1e7)
    _log.addHandler(_buffer)
    _buffers[name] = _buffer
    
def debuffer_logger(name=None):
    """Debuffer a given logger.
    
    :param name: The name of the logger to debuffer.
    
    This method will atempt to dump all of the messages from a logger's
    :class:`BufferHandler` into its other handlers. Then it will remove the
    buffer from the logger."""
    logger = logging.getLogger(name)
    name = "__root__" if name is None else name
    debuffer = _buffers.get(name,False)
    if not debuffer:
        for handler in logger.handlers:
            if isinstance(handler,BufferHandler):
                debuffer = handler
                break
    if not debuffer:
        return
    
    # Since loggers have a .handle() method, they can be
    # set as targets for the debuffer command.
    debuffer.setTarget(logger)
    
    logger.removeHandler(debuffer)
    debuffer.close()
    
class PyshellLogger(logging.getLoggerClass()):
    """
    This is a logger object which can act as the 
    """
    
    
    def __getattr__(self,name):
        """Return special level functions."""
        if name.upper() not in logging._levelNames:
            raise AttributeError("{0} has no attribute {1}".format(self,name))
        def log(msg, *args,**kwargs):
            self._log(logging._levelNames[name.upper()],msg,args,**kwargs)
        log.__doc__ = "Log a message at level {}".format(name)
        return log

logging.setLoggerClass(PyshellLogger)

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
                notifications=list(self.mapping.values()),
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
        
    
    mapping = {
        logging.DEBUG:"Debug Message",
        logging.INFO:"Info Message",
        logging.WARNING:"Warning Message",
        logging.CRITICAL:"Critical Message",
        logging.ERROR:"Error Message",
        }

    
    
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
        if record.levelno < logging.DEBUG:
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
        if hasattr(target,"handle"):
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
    
def _showwarning(message, category, filename, lineno, file=None, line=None):
    """docstring for showwarning"""
    logger = getLogger("py.warnings")
    if logger.isEnabledFor(logging.WARN):
        if category != UserWarning:
            s = "{0}: {1} ({2}:{3})".format(category.__name__, message, os.path.basename(filename), lineno)
        else:
            s = "{0}".format(message)
        logger._log(30,s,tuple())

_warnings_showwarning = None

def captureWarnings(capture):
    """
    If capture is true, redirect all warnings to the logging package.
    If capture is False, ensure that warnings are not redirected to logging
    but to their original destinations.
    """
    global _warnings_showwarning
    if capture:
        if _warnings_showwarning is None:
            _warnings_showwarning = warnings.showwarning
        warnings.showwarning = _showwarning
    else:
        warnings.showwarning = _warnings_showwarning
        if _warnings_showwarning is not None:
            _warnings_showwarning = None
            
logging.captureWarnings = captureWarnings
        
    
logging.addLevelName(25,'STATUS')

this = sys.modules[__name__]
for l,n in logging._levelNames.items():
    if isinstance(l,int):
        setattr(this,n,l)
    
        