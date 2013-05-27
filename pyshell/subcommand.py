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

This module provides scaffolding for subcommand classes. Individual subcommands are defined in :class:`SCEngine`. :class:`SCEngine` is a drop-in replacement for :class:`~pyshell.base.CLIEngine`. Then add each class to the :attr:`SCController.subEngines` list on a subclass of :class:`SCController`. :class:`SCController` can be run the same way :class:`~pyshell.base.CLIEngine` works. Both :class:`SCController` and :class:`SCEngine` are subclasses of :class:`~pyshell.base.CLIEngine` and should behave naturally with a :class:`~pyshell.base.CLIEngine`-style configuration.

Base Class API Documentation
----------------------------

.. autoclass::
    SCEngine
    :members:
    :exclude-members: start, end
    :inherited-members:
    
.. autoclass::
    SCController
    :members:
    :exclude-members: start, end
    :inherited-members:

"""
from . import CLIEngine

import sys
from argparse import Action, SUPPRESS, RawDescriptionHelpFormatter

__all__ = ['SCEngine','SCController']

class SCEngine(CLIEngine):
    """A base engine for use as a subcommand or stand-alone command like :class:`~pyshell.base.CLIEngine`. When used as a sub-command, it should be attached to a :class:`SCController` to act as the base command.
    
    :param command: The command name for this object. It can also be set as a class attribute: `cls.command` It cannot be changed once the program has initialized.
    
    
    """
    
    supercfg = []
    
    defaultcfg = False
    
    def __init__(self, command=None, **kwargs):
        prefix_chars = kwargs.pop('prefix_chars',"-")
        super(SCEngine, self).__init__(prefix_chars=prefix_chars)
        self._hasinit = False
        self.command = command if command is not None else getattr(self,'command',"")
        self._kwargs = kwargs
        self._supercommand = False
        
    @property
    def help(self):
        """The help for this sub-parser or parses"""
        return None
    
    def __parser__(self,subparsers):
        """Set the parser for this subcommand."""
        self._kwargs.setdefault('help',self.help)
        self._kwargs.setdefault('description',self.description)
        self._kwargs.setdefault('add_help',False)
        self._kwargs.setdefault('formatter_class',RawDescriptionHelpFormatter)
        self._parser = subparsers.add_parser(self.command,**self._kwargs)
        self._hasinit = True
        
    def __parse__(self,opts):
        """Save options for this subcommand."""
        self._opts = opts
        
    def __superconfig__(self, config, opts):
        """Configure this subcommand."""
        self._config = config
        if self.defaultcfg:
            self.config.configure(module=self.module,defaultcfg=self.defaultcfg,cfg=self.defaultcfg)
        self._opts = opts
        self._add_help()
        
    def init(self):
        """Post-initialization functions. These will be run after the sub-parser is established."""
        super(SCEngine, self).init()
        
        
    def parse(self):
        """Parse. By default, does nothing if this object is a subcommand."""
        if not self._supercommand:
            super(SCEngine, self).parse()
        
            
    def configure(self):
        """Configure this object. Does nothing if this object is a subcommand."""
        if not self._supercommand:
            super(SCEngine, self).configure()
        else:
            self.config.configure(module=self.__module__,defaultcfg=self.defaultcfg,cfg=False,supercfg=self.supercfg)
        
    
class _LimitedHelpAction(Action):
    """Only print the help when the action is triggered without a sub-command"""
    def __init__(self,
                 option_strings,
                 dest=SUPPRESS,
                 default=SUPPRESS,
                 help=None):
        super(_LimitedHelpAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)
    def __call__(self, parser, namespace, values, option_string=None):
        if not getattr(namespace,'mode',False):
            parser.print_help()
            parser.exit()
    

class SCController(CLIEngine):
    """An engine for the creation of python packages"""
    
    _subEngines = []
    
    _subparsers_help = "sub-command help"
    
    def __init__(self,**kwargs):
        kwargs.setdefault('conflict_handler','resolve')
        super(SCController, self).__init__(**kwargs)
        self._add_limited_help()
        self._subcommand = {}
        for subEngine in self._subEngines:
            subCommand = subEngine()
            subCommand._supercommand = self
            self._subcommand[subCommand.command] = subCommand
            # This is important, as it passes the subCommand's super configuration on.
            # We might want something that passes the full configuration chain down...
            self.supercfg += subCommand.supercfg
        if self._subEngines:
            self._subparsers = self._parser.add_subparsers(dest='mode',help=self._subparsers_help)
        else:
            raise AttributeError("%r No SubEngines attached." % self)
        for subEngine in self._subcommand:
            self._subcommand[subEngine].__parser__(self._subparsers)
            self._subcommand[subEngine].init()
        
    def _add_limited_help(self):
        """Add a limited help function"""
        self.__help_action = self.parser.add_argument('-h','--help',action=_LimitedHelpAction,help="Display this help text.")
        
    @property
    def mode(self):
        """Return the mode"""
        return getattr(self.opts,'mode',False)
        
    @property
    def subcommand(self):
        """The active subcommand."""
        return self._subcommand[self.mode]
        
    def start(self):
        self.subcommand.start()
        
    def do(self):
        """Call the subcommand :meth:`~SCEngine.do` method."""
        self.subcommand.do()
        
    def end(self):
        self.subcommand.end()
        
    def kill(self):
        """Killing mid-command, calls the active subcommand :meth:`~SCEngine.kill` method."""
        self.subcommand.kill()
        self._exitcode = 1
    
    def parse(self):
        """Parse command line args"""
        if len(self._subcommand) and hasattr(self._opts,'mode'):
            # This code is present because parse_known_args() doesn't
            # play well with sub-parsers. If the sub-parser is triggered,
            # it won't get parsed again.
            self._rargs.insert(0,self._opts.mode)
            delattr(self._opts,'mode')
        self._opts = self.parser.parse_args(self._rargs, self._opts)
        self.configure_logging()
        self.subcommand.__parse__(self._opts)
        self.subcommand.parse()
        
    def configure(self):
        """Configure the package creator"""
        super(SCController, self).configure()
        self.subcommand.__superconfig__(self._config,self._opts)
        self.subcommand.configure()
        
        
