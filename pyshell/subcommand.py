# -*- coding: utf-8 -*-
# 
#  subcommand.py
#  pyshell
#  
#  Created by Alexander Rudy on 2012-11-18.
#  Copyright 2012 Alexander Rudy. All rights reserved.
# 
"""
.. currentmodule: pyshell.subcommand

:mod:`subcommand` – Creating commands with Subcommands
======================================================


Base Class API Documentation
============================



.. autoclass::
    SCEngine
    :members:
    :inherited-members:
    
.. autoclass::
    SCController
    :members:
    :inherited-members:

"""
from .base import CLIEngine

import sys

class SCEngine(CLIEngine):
    """A base engine for use as a subcommand to CLIEngine"""
    
    supercfg = []
    
    def __init__(self, command, **kwargs):
        prefix_chars = kwargs.pop('prefix_chars',"-")
        super(SCEngine, self).__init__(prefix_chars=prefix_chars)
        self.command = command
        self._kwargs = kwargs
        self._supercommand = False
        
    @property
    def help(self):
        """The help for this sub-parser or parses"""
        return None
    
    def __parser__(self,subparsers):
        """Set the parser for this subcommand."""
        self._kwargs.setdefault('help',self.help)
        self._parser = subparsers.add_parser(self.command,**self._kwargs)
        
    def __parse__(self,opts):
        """Save options for this subcommand."""
        self._opts = opts
        
    def __superconfig__(self, config, opts):
        """Configure this subcommand."""
        self._config = config
        if self.defaultcfg:
            self.config.configure(module=self.module,defaultcfg=self.defaultcfg)
        self._opts = opts
        
    def parse(self):
        """Parse. By default, does nothing if this object is a subcommand."""
        if not self._supercommand:
            super(SCEngine, self).parse()
        
            
    def configure(self):
        """Configure this object. Does nothing if this object is a subcommand."""
        if not self._supercommand:
            super(SCEngine, self).configure()
        
        
    

class SCController(CLIEngine):
    """An engine for the creation of python packages"""
    
    _subEngines = []
    
    _subparsers_help = "sub-command help"
    
    def __init__(self,**kwargs):
        super(SCController, self).__init__(**kwargs)
        self._subcommand = {}
        for subEngine in self._subEngines:
            # For specific cases, where the master engine sets the module name, pass that module name
            # on to subEngines before they are instantiated.
            if not hasattr(subEngine,'module') or getattr(subEngine.module,'__isabstractmethod__',False):
                subEngine.module = self.module
            # Since type-instatiation has already happened, we hook into the shenanigans below.
            # TODO: Degrade gracefully for python<2.7
            if isinstance(getattr(subEngine,'__abstractmethods__',None),frozenset):
                abm = set(subEngine.__abstractmethods__)
                if 'module' in abm:
                    abm.remove('module')
                    subEngine.__abstractmethods__ = frozenset(abm)
            subCommand = subEngine()
            subCommand._supercommand = self
            self._subcommand[subCommand.command] = subCommand
            self.supercfg += subCommand.supercfg
        if self._subEngines:
            self._subparsers = self._parser.add_subparsers(dest='mode',help=self._subparsers_help)
        for subEngine in self._subcommand:
            self._subcommand[subEngine].__parser__(self._subparsers)
        
        
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
        self._exitcode = 1
    
    def parse(self):
        """Parse command line args"""
        if len(self._subcommand) and hasattr(self._opts,'mode'):
            # This code is present because parse_known_args() doesn't
            # play well with sub-parsers. If the sub-parser is triggered,
            # it won't get parsed again.
            self._rargs.insert(0,self._opts.mode)
            delattr(self._opts,'mode')
        super(SCController, self).parse()
        for subEngine in self._subcommand:
            self._subcommand[subEngine].__parse__(self._opts)
            self._subcommand[subEngine].parse()
        
    def configure(self):
        """Configure the package creator"""
        super(SCController, self).configure()
        for subEngine in self._subcommand:
            self._subcommand[subEngine].__superconfig__(self._config,self._opts)
            self._subcommand[subEngine].configure()
            
            
