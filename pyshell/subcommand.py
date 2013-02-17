# -*- coding: utf-8 -*-
# 
#  subcommand.py
#  pyshell
#  
#  Created by Alexander Rudy on 2012-11-18.
#  Copyright 2012 Alexander Rudy. All rights reserved.
# 

from .base import CLIEngine

import sys

class SCEngine(object):
    """A base engine for use as a subcommand to CLIEngine"""
    
    supercfg = []
    
    def __init__(self, command, **kwargs):
        super(SCEngine, self).__init__()
        self.command = command
        self._kwargs = kwargs
        
    @property
    def help(self):
        """Return the help"""
        return None
        
    @property
    def config(self):
        """docstring for config"""
        return self._config
        
    @property
    def parser(self):
        """docstring for parser"""
        return self._parser
        
    @property
    def opts(self):
        """docstring for opts"""
        return self._opts
    
    def setup_parser(self,subparsers):
        """docstring for parser"""
        self._kwargs.setdefault('help',self.help)
        self._parser = subparsers.add_parser(self.command,**self._kwargs)
        
    def parse(self,opts):
        """docstring for parse"""
        self._opts = opts
        
    def __superconfig__(self, config, opts):
        """docstring for __superconfig__"""
        self._config = config
        self._opts = opts
        
    def configure(self):
        """Configure this object."""
        pass
        
    def start(self):
        """docstring for start"""
        pass
        
    def do(self):
        """docstring for do"""
        pass
        
    def end(self):
        """docstring for end"""
        pass
        
    def kill(self):
        """docstring for kill"""
        pass
        
class SCController(CLIEngine):
    """An engine for the creation of python packages"""
    
    _subEngines = []
    
    _subparsers_help = "sub-command help"
    
    def __init__(self):
        super(SCController, self).__init__()
        self._subcommand = {}
        for subEngine in self._subEngines:
            subCommand = subEngine()
            self._subcommand[subCommand.command] = subCommand
            self.supercfg += subCommand.supercfg
        
    def start(self):
        """docstring for start"""
        self._subcommand[self._opts.mode].start()
        
    def do(self):
        """docstring for start"""
        self._subcommand[self._opts.mode].do()
        
    def end(self):
        """docstring for end"""
        self._subcommand[self._opts.mode].end()
        
    def kill(self):
        """Killing mid-command"""
        self._subcommand[self._opts.mode].kill()
        sys.exit(1)
        
    def parse(self):
        """Parse command line args"""
        super(SCController, self).parse()
        for subEngine in self._subcommand:
            self._subcommand[subEngine].parse(self._opts)
        
    def configure(self):
        """Configure the package creator"""
        super(SCController, self).configure()
        self._subparsers = self._parser.add_subparsers(dest='mode',help=self._subparsers_help)
        for subEngine in self._subcommand:
            self._subcommand[subEngine].setup_parser(self._subparsers)
            self._subcommand[subEngine].__superconfig__(self._config,self._opts)
            self._subcommand[subEngine].configure()
            
            
