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

Using the :class:`CLIEngine`
============================

The :class:`CLIEngine` is designed with "Convention over Configuration" \
in mind. That is, it aims to set everything up so that it will work out\
-of-the-box, and the user is responsbile for adjusting undesireable \
behavior.

Class Construction
------------------
    
This class should be subclassed by the user, who should re-implement \
the following methods:
    
- :meth:`~CLIEngine.do`  - Does the 'real work'.
- :meth:`~CLIEngine.kill` - Called if the engine tries to exit abnormally.
    
These funcitons are used in the normal operation of the command line engine.
    

The user should also override the desired instance variables on the class. `module` must be overridden.

Other methods are used to control the engine.
    
Using the Engine
----------------

To run the engine, use :meth:`~CLIEngine.run`. To run the engine without \
instantiating the class, use :meth:`~CLIEngine.script`, a class method \
that instantiates a new object, and runs the tool. Both methods \
accomplish the same thing at the end of the day.

You can use :meth:`~CLIEngine.script` to start the engine with the "if main" \
python convention ::

    if __name__ == '__main__':
        Engine.script()

Using :meth:`~CLIEngine.script` allows the developer to set this as \
an entry point in their ``setup.py`` file, and so provide the command \
line enegine as a command line tool in a distutils supported python package. \
A basic entry point for this tool would appear like ::
    
    ["PyScript = mymodule.cli:Engine.script"]
    

Engine Operation
----------------

The engine is set up to use a configuration file system, \
provide basic parsing attributes, and an interruptable \
command line interaction flow. The configuration is designed \
to provide dynamic output and to configure the system \
before it completes the parsing process.
    
1. Initialization loads the object, and sets up the argument parser. \
At this point, parser should only understand arguments that are neeeded \
to print the best `--help` message.
    
2. Preliminary Arguments are parsed by :meth:`arguments`.
    
3. Configuration is handled by the :meth:`configure` function. This \
function loads the following configuration files in order (such that the \
last one loaded is the one that takes precedence):
    
* The ``defaultcfg`` file from ``engine.__module__``. This allows the \
developer to provide a base configuration for the engine.
* The requested configuration file from the user's home directory.
* The requested configuration file form the current directory.
* If no configuration file is requested, the filename for `defaultcfg` will be \
used. As well, if the engine cannot find the requested configureation file \
in the current directory (i.e. the user asks for a file, and it isn't there) \
a warning will be issued.
    
4. Help message is inserted into parsing, and remining arguments\
parsed by :meth:`parse`. At this point, the entire configuration process \
is complete.
    
5. The function :meth:`do` is called, \
This should do the bulk of the engine's work.

6. If the user interrupts the operation of the program, :meth:`kill` will \
be called. If python is in ``__debug__`` mode, this will raise a full \
traceback. If not, the traceback will be suppressed.


:mod:`base` - Command Line Interface Engine
===========================================

.. autoclass::
    CLIEngine
    :members:
    

Call structure of :meth:`run`
=============================
The call structure of the method :meth:`run`, the main script driver::
    
    if not(hasattr(self, '_rargs') and hasattr(self, '_opts')):
        warn("Implied Command-line mode", UserWarning)
        self.arguments()
    self.configure()
    self.parse()
    try:
        self.do()
    except (KeyboardInterrupt, SystemExit):
        self.kill()
    



"""

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pkg_resources import resource_filename
import os, os.path
import abc
from warnings import warn
from .config import StructuredConfiguration as Config, Configuration as BConfig
import logging, logging.config

__all__ = ['CLIEngine']

class CLIEngine(object):
    """A base class for Command Line Inteface facing tools. :class:`CLIEnigne` \
    provides the basic structure to set up a simple command-line interface,\
    based on the :mod:`argparse` framework.
    
    :param str prefix_chars: Sets the prefix characters to command line arguments. \
    by default this is set to "-", reqiuring that all command line argumetns begin \
    with "-".
    
    At the end of initialization, the configuration (:attr:`config`) and \
    :attr:`parser` will be availabe for use.
    """
    
    __metaclass__ = abc.ABCMeta
    
    description = "A command line interface."
    """The textual description of the command line interface, \
    set as the description of the parser from :mod:`argparse`."""
    
    epilog = ""
    """The text that comes at the end of the :mod:`argparse` \
    help text."""
    
    defaultcfg = "Config.yml"
    """The name of the default configuration file to be loaded. If set to \
    ``False``, no configuration will occur."""
    
    supercfg = []
    
    PYSHELL_LOGGING = [('pyshell','logging.yml')]
    """This constant item can be added to the superconfiguration :attr:`supercfg` to enable a default logging configuration setup. It should probably be added first, so that your own code will override it."""
    
    PYSHELL_LOGGING_STREAM = [('pyshell','logging-stream-only.yml')]
    """This constant item can be added to the superconfiguration :attr:`supercfg` to enable a default logging configuration setup. It should probably be added first, so that your own code will override it. It only provides stream loggers, not file handlers."""
    
    def __init__(self, prefix_chars='-', conflict_handler='error'):
        super(CLIEngine, self).__init__()
        self._parser = ArgumentParser(
            prefix_chars = prefix_chars, add_help = False,
            formatter_class = RawDescriptionHelpFormatter,
            description = self.description,
            epilog = self.epilog,
            conflict_handler = conflict_handler)
        self._home = os.environ["HOME"]
        self._config = Config()
        self._config.dn = BConfig
        self._opts = None
        self._rargs = None
        self.exitcode = 0
        self._hasinit = True
        
    def init(self):
        """Initialization after the parser has been created."""
        if self.defaultcfg:
            self.parser.add_argument('--config',
                action='store', metavar='file.yml', default=self.defaultcfg,
                help="Set configuration file. By default, load %(file)s and"\
                " ~/%(file)s if it exists." % dict(file=self.defaultcfg))
        
    @property
    def parser(self):
        """:class:`argparse.ArgumentParser` instance for this engine."""
        if getattr(self,'_hasinit',False):
            return self._parser
        else:
            raise AttributeError("Parser has not yet been initialized!")
        
    @property
    def config(self):
        """:class:`pyshell.config.Configuration` object for this engine."""
        return self._config
        
    @property
    def opts(self):
        """Command Line Options, as paresed, for this engine"""
        return self._opts
        
    def parse(self):
        """Parse the command line arguments"""
        self._add_help()
        self._opts = self.parser.parse_args(self._rargs, self._opts)
        self.configure_logging()
    
    def _remove_help(self):
        """Remove the ``-h, --help`` argument. This is a dangerous swizzle!"""
        for option_string in self.__help_action.option_strings:
            del self._parser._option_string_actions[option_string]
        self._parser._remove_action(self.__help_action)
    
    def _add_help(self):
        """Add the ``-h, --help`` argument."""
        self.__help_action = self.parser.add_argument('-h', '--help',
            action='help', help="Display this help text")
    
    def configure_logging(self):
        """Configure the logging system."""
        if "logging" in self.config:
            logging.config.dictConfig(self.config["logging"])
            if "py.warnings" in self.config["logging.loggers"]:
                logging.captureWarnings(True)
            
    def arguments(self, *args):
        """Parse the given arguments. If no arguments are given, parses \
        the known arguments on the command line. Generally this should \
        parse all arguments except ``-h`` for help, which should be \
        parsed last after the help text has been fully assembled. The full \
        help text can be set to the ``self.parser.epilog`` attribute.
        
        :param \*args: The arguments to be parsed. 
        
        Similar to taking the command line components and doing \
        ``" -h --config test.yml".split()``. Same signature as would be used \
        for :meth:`argparse.ArgumentParser.parse_args()`
        
        """
        self._opts, self._rargs = self.parser.parse_known_args(*args)        
        
    
    def configure(self):
        """Configure the command line engine from a series of YAML files.
        
        The configuration loads (starting with a blank configuration):
        
            1. The :attr:`module` configuration file named for \
            :attr:`defaultcfg`
            2. The command line specified file from the user's home folder \
            ``~/config.yml``
            3. The command line specified file from the working directory.
        
        If the third file is not found, and the user specified a new name for \
        the configuration file, then the user is warned that no configuration \
        file could be found. This way the usre is only warned about a missing \
        configuration file if they requested a file specifically (and so \
        intended to use a customized file).
        
        """
        cfg = getattr(self.opts,'config',self.defaultcfg)
        self.config.configure(module=self.__module__,defaultcfg=self.defaultcfg,cfg=cfg,supercfg=self.supercfg)
                    
    
    def start(self):
        """This function is called at the start of the :class:`CLIEngine` \
        operation. It should contain any process spawning that needs to \
        occur."""
        pass
        
    def do(self):
        """This function should handle the main operations for the command \
        line tool."""
        pass
        
    def end(self):
        """This function is called at the end of the :class:`CLIEngine` \
        operation and should ensure that all subprocesses have ended."""
        pass
        
    def kill(self):
        """This function should forcibly kill any subprocesses."""
        pass
            
    def run(self):
        """This method is used to run the command line engine in the expected \
        order. This method should be called to run the engine from another \
        program."""
        if not(hasattr(self, '_rargs') and hasattr(self, '_opts')):
            warn("Implied Command-line mode", UserWarning)
            self.arguments()
        self.configure()
        self.parse()
        try:
            self.start()
            self.do()
            self.end()
        except SystemExit as e:
            if not getattr(e,'code',0):
                self.kill()
            if __debug__:
                raise
        except KeyboardInterrupt as e:
            self.kill()
            if __debug__:
                raise
        return self.exitcode
    
    @classmethod        
    def script(cls):
        """The class method for using this module as a script entry \
        point. This method ensures that the engine runs correctly on \
        the command line, and is cleaned up at the end."""
        engine = cls()
        engine.init()
        engine.arguments()
        return engine.run()