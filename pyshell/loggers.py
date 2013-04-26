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

import logging
import logging.handlers as handlers

import math
import copy
import sys
import time
import os
import yaml
import collections

from .console import get_color

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
        
        
        
        
        