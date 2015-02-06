# -*- coding: utf-8 -*-
# 
#  subcommand.py
#  pyshell
#  
#  Created by Alexander Rudy on 2012-11-18.
#  Copyright 2012 Alexander Rudy. All rights reserved.
# 
"""

The two classes in :mod:`pyshell.subcommand` are for the creation of sub-commands (:class:`SCEngine`),
and controllering those subcommands (:class:`SCController`). The API for both is based on :class:`~pyshell.CLIEngine`.

.. inheritance-diagram::
    pyshell.subcommand.SCEngine
    pyshell.subcommand.SCController
    :parts: 1


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

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)

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
        self._command = command if command is not None else getattr(self,'_command',"")
        self._kwargs = kwargs
        self._supercommand = False
        
    @property
    def command(self):
        """docstring for command"""
        return self._command
        
        
    @command.setter
    def command(self,value):
        """docstring for command"""
        if not self._hasinit:
            self._command = value
        else:
            raise AttributeError("Cannot change command name once parsers have initialized.")
        
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
        setattr(self, type(self).config._attr, config)
        if self.defaultcfg:
            self.config.configure(module=self.__module__, defaultcfg=self.defaultcfg, cfg=self.defaultcfg)
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
    """A controller for a set of :class:`SCEngine` objects. This class provides the
    controller for individual subcommand objects.
    
    THe initialization of this class takes keyword arguments that can be passed through to
    :class:`pyshell.CLIEngine`. This class can be used as an engine in-and-of itself. To access
    the currently active subcommand, you can use the :attr:`SCController.subcommand`. If you wish
    to replace the :meth:`SCController.do` method, you can either use the python :func:`suepr`
    method, or call ``self.subcommand.do()`` at the appropriate point.
    """
    
    subEngines = []
    """A list of :class:`SCEngine` subclasses which define the subcommands
    for this engine. This is the only attribute required for a working :class:`SCController`.
    """
    
    _subparsers_help = "sub-command help"
    
    def __init__(self,**kwargs):
        kwargs.setdefault('conflict_handler','resolve')
        if hasattr(self,'_subEngines'):
            self.subEngines = self._subEngines
        super(SCController, self).__init__(**kwargs)
        self._add_limited_help()
        self._subcommand = {}
        for subEngine in self.subEngines:
            subCommand = subEngine()
            subCommand._supercommand = self
            self._subcommand[subCommand.command] = subCommand
            # This is important, as it passes the subCommand's super configuration on.
            # We might want something that passes the full configuration chain down...
            self.supercfg += subCommand.supercfg
        if self.subEngines:
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
        
    def do(self):
        """Call the subcommand :meth:`~SCEngine.do` method."""
        self.subcommand.do()
        
    def kill(self):
        """Killing mid-command, calls the active subcommand :meth:`~SCEngine.kill` method."""
        self.subcommand.kill()
        self._exitcode = 1
    
    def parse(self):
        """Parse command line args"""
        if len(self._subcommand) and hasattr(self.opts,'mode'):
            # This code is present because parse_known_args() doesn't
            # play well with sub-parsers. If the sub-parser is triggered,
            # it won't get parsed again.
            self._rargs.insert(0,self.opts.mode)
            delattr(self._opts,'mode')
        self._opts = self.parser.parse_args(self._rargs, namespace=self._opts)
        self.configure_logging()
        self.subcommand.__parse__(self._opts)
        self.subcommand.parse()
        
    def configure(self):
        """Configure the package creator"""
        super(SCController, self).configure()
        self.subcommand.__superconfig__(self.config,self._opts)
        self.subcommand.before_configure()
        self.subcommand.configure()
        self.subcommand.after_configure()
        
class SCFEngine(CLIEngine):
    """A subcontroller engine which uses named functions as the targets for subcommands."""
    def __init__(self, arg):
        super(SCFEngine, self).__init__()
        self.arg = arg
        
