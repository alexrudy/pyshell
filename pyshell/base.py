# -*- coding: utf-8 -*-
# 
#  base.py
#  jaberwocky
#  
#  Created by Jaberwocky on 2012-10-16.
#  Copyright 2012 Jaberwocky. All rights reserved.
# 
"""
.. currentmodule: pyshell.base

:mod:`base` - Command Line Interface Engine
===========================================

.. autoclass::
    CLIEngine
    :members:
    
"""
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pkg_resources import resource_filename
import os, os.path
from warnings import warn
from .config import DottedConfiguration as Config

class CLIEngine(object):
    """The controlling engine for backups."""
    
    description = "A command line interface."
    
    defaultcfg = "Config.yml"
    
    def __init__(self):
        super(CLIEngine, self).__init__()
        self._parser = ArgumentParser(
            prefix_chars = '-', add_help = False,
            formatter_class = RawDescriptionHelpFormatter,
            description = self.description)
        if self.defaultcfg:
            self._parser.add_argument('--config',
                action='store', metavar='file.yml', default=self.defaultcfg,
                help="Set configuration file. By default, load %(file)s and"\
                " ~/%(file)s if it exists." % dict(file=self.defaultcfg))
        self._home = os.environ["HOME"]
        self._config = Config()
        self._config.dn = Config
        self._opts = None
        self._rargs = None
        
        
    @property
    def config(self):
        """Configuration"""
        return self._config
        
    def parse(self):
        """Parse the command line arguments"""
        self._parser.add_argument('-h', '--help',
            action='help', help="Display this help text")
        self._opts = self._parser.parse_args(self._rargs, self._opts)
            
    def arguments(self, *args):
        """Parse the given arguments"""
        self._opts, self._rargs = self._parser.parse_known_args(*args)        
        
    
    def configure(self):
        """Configure the simulator"""
        if not self.defaultcfg:
            return
        self._config.load(resource_filename(__name__, self.defaultcfg))
        if hasattr(self._opts, 'config') \
            and os.path.exists(os.path.expanduser("~/%s" % self._opts.config)):
            self._config.load(os.path.expanduser("~/%s" % self._opts,
                'config'))
        if hasattr(self._opts, 'config') and os.path.exists(self._opts.config):
            self._config.load(self._opts.config, silent=False)
        elif hasattr(self._opts, 'config') \
            and self._opts.config != self.defaultcfg:
            warn("Configuration File not found!", RuntimeWarning)
                    
    
    def start(self):
        """Start this system."""
        raise NotImplementedError("Nothing to Start!")
        
    def end(self):
        """End this tool"""
        raise NotImplementedError("Nothing to End!")
        
    def kill(self):
        """Kill this tool"""
        raise NotImplementedError("Nothing to Kill!")
            
    def run(self):
        """Run the whole engine"""
        if not(hasattr(self, '_rargs') and hasattr(self, '_opts')):
            warn("Implied Command-line mode", UserWarning)
            self.arguments()
        self.configure()
        self.parse()
        try:
            self.start()
            self.end()
        except (KeyboardInterrupt, SystemExit):
            self.kill()
    
    @classmethod        
    def script(cls):
        """Operations if this module is a script"""
        engine = cls()
        engine.arguments()
        engine.run()