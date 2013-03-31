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

from pyshell import CLIEngine
import os

class Hello(CLIEngine):
    """Say hello in English, French, or another language."""
    
    defaultcfg = "hello.yml"
    
    description = "Say hello!"
    
    def init(self):
        """Arguments to be set up at the beginning. By default, this function will set up the --config argument."""
        super(Hello, self).init()
        self.parser.add_argument("-f",dest='flourish',action='store_true',help=u"Add a little flourish!")
        self.parser.add_argument("--name",action='store',type=unicode,default=unicode(os.environ["USER"]),
            help=u"Set the name. (Default '{:s}')".format(os.environ["USER"]))
        
    def configure(self):
        """Configure the engine for operation, before help will be printed."""
        super(Hello, self).configure()
        
        # Here we overwrite any basic configuration items. Really, these should go
        # in 'hello.yml', the configuration file.
        self.config["Language"].update(
            {   'English' : u"Hello",
                'Spanish' : u"Hola",
            }
        )
        
        self.parser.add_argument("language",action='store')
        # We add this argument here, becauase it is required.
        
        self.parser.add_argument("-t","--title",action='store',default=self.config["Address"],type=unicode,
            help=u"Change from the default title '{:s}'".format(self.config["Address"]),metavar="MR")
        # We add this argument here because it uses information from the configuration.
        
    def parse(self):
        """Do any parsing"""
        super(Hello, self).parse()
        if self.opts.language not in self.config["Language"]:
            self.parser.error(u"Language '{:s}' not understood.".format(self.opts.language))
        self.opts.greeting = self.config["Language"].get(self.opts.language)
        self.opts.punct = u"!" if self.opts.flourish else u"."
        self.opts.name = self.opts.name.capitalize()
        
    def do(self):
        """Take the actual action"""
        print(u"{0.greeting:s}, {0.title:s} {0.name:s}{0.punct:s}".format(self.opts))
        
        
if __name__ == '__main__':
    Hello.script()
    