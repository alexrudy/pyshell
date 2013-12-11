# -*- coding: utf-8 -*-
# 
#  base.py
#  jaberwocky
#  
#  Created by Jaberwocky on 2012-10-16.
#  Copyright 2012 Jaberwocky. All rights reserved.
# 
"""
The :class:`CLIEngine` objects use :mod:`abc` to provide pythonic abstract base class features.
The only abstract method in :class:`CLIEngine` is the :meth:`CLIEngine.do` method.

.. inheritance-diagram::
    CLIEngine
    :parts: 1

"""

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)


from argparse import ArgumentParser, RawDescriptionHelpFormatter
import os, os.path
import abc
from warnings import warn
from .config import StructuredConfiguration
from .config.helpers import bind_configuration_action, ConfigurationProperty
from .util import semiabstractmethod, deprecatedmethod
from .loggers import configure_logging, getLogger, PYSHELL_LOGGING, PYSHELL_LOGGING_STREAM, PYSHELL_LOGGING_STREAM_ALL
from six import with_metaclass
import six

__all__ = [ 'CLIEngine',
    'PYSHELL_LOGGING','PYSHELL_LOGGING_STREAM','PYSHELL_LOGGING_STREAM_ALL']



@six.add_metaclass(abc.ABCMeta)
class CLIEngine(object):
    """A base class for Command Line Inteface facing tools. :class:`CLIEnigne` 
    provides the basic structure to set up a simple command-line interface,
    based on the :mod:`argparse` framework. The only required implementation 
    below is the :meth:`do` method. All other settings are optional.
    
    :param str prefix_chars: Sets the prefix characters to command line arguments. 
        by default this is set to "-", reqiuring that all command line argumetns begin 
        with "-".
    
    At the end of initialization, the configuration (:attr:`config`) and 
    :attr:`parser` will be availabe for use.
    """
    # pylint: disable= too-many-instance-attributes
        
    @property
    def description(self):
        """The textual description of the command line interface, 
        set as the description of the parser from :mod:`argparse`."""
        return self.__doc__
        
    debug = __debug__
    """Whether this tool will show stack traces."""
        
    epilog = ""
    """The text that comes at the end of the :mod:`argparse` 
    help text."""
    
    defaultcfg = "Config.yml"
    """The name of the default configuration file to be loaded. If set to 
    ``False``, no configuration will occur."""
    
    supercfg = []
    """This is a list of tuples which represent configurations that should be 
    loaded before the default configuration is loaded. Each tuple contains the 
    module name and filename pair that should be passed to 
    :func:`~pkg_resources.resource_filename`. To specify a super-configuration 
    in the current directory, use ``__main__`` as the module name."""
    
    def __init__(self, prefix_chars=str("-"), 
        conflict_handler='error'):
        super(CLIEngine, self).__init__()
        self._log = getLogger(self.__module__)
        self._parser = ArgumentParser(
            prefix_chars = prefix_chars, add_help = False,
            formatter_class = RawDescriptionHelpFormatter,
            description = self.description,
            epilog = self.epilog,
            conflict_handler = conflict_handler)
        self._home = os.environ["HOME"]
        self.config = StructuredConfiguration()
        self._opts = None
        self._rargs = None
        self.__help_action = None
        self.exitcode = 0
        self._hasinit = False
        self._hasargs = False
        self._hasvars = True
        
    
    config = ConfigurationProperty()
    
    @property
    def parser(self):
        """:class:`argparse.ArgumentParser` instance for this engine."""
        if getattr(self, '_hasvars', False):
            return self._parser
        else:
            raise AttributeError("Parser has not yet been initialized!")
        
    
    @property
    def opts(self):
        """Command Line Options, as paresed, for this engine"""
        return self._opts
        
    @property
    def log(self):
        """This engine's logger"""
        return self._log
        
    def init(self):
        """Initialization after the parser has been created."""
        self._hasinit = True
        if self.defaultcfg:
            self._add_configfile_args()
            self._add_configure_args()
        
    
    def arguments(self, *args):
        r"""Parse the given arguments. If no arguments are given, parses 
        the known arguments on the command line. Generally this should 
        parse all arguments except ``-h`` for help, which should be 
        parsed last after the help text has been fully assembled. The full 
        help text can be set to the ``self.parser.epilog`` attribute.
        
        :param \*args: The arguments to be parsed.
        
        Similar to taking the command line components and doing 
        ``" -h --config test.yml".split()``. Same signature as would be used 
        for :meth:`argparse.ArgumentParser.parse_args()`
        
        """
        if not self._hasinit:
            self.init()
        self._opts, self._rargs = self.parser.parse_known_args(*args)        
        self._hasargs = True
    
    def before_configure(self):
        """Actions to be run before configuration. This method can be 
        overwritten to provide custom actions to be taken before the
        engine gets configured.
        """
        pass
    
    def configure(self):
        """Configure the command line engine from a series of YAML files.
        
        The configuration loads (starting with a blank configuration):
        
            1. The :attr:`module` configuration file named for 
            :attr:`defaultcfg`
            2. The command line specified file from the user's home folder 
            ``~/config.yml``
            3. The command line specified file from the working directory.
        
        If the third file is not found, and the user specified a new name for 
        the configuration file, then the user is warned that no configuration 
        file could be found. This way the usre is only warned about a missing 
        configuration file if they requested a file specifically (and so 
        intended to use a customized file).
        
        """
        cfg = getattr(self.opts, 'config', self.defaultcfg)
        self.config.configure(module=self.__module__,
            defaultcfg=self.defaultcfg, cfg=cfg,supercfg=self.supercfg)
        self.config.parse_literals(*getattr(self.opts, 'configure', []))
        
    def after_configure(self):
        """Actions to be run after configuration. This method can be 
        overwritten to provide custom actions to be taken before the
        engine gets configured."""
        pass
        
    def parse(self):
        """Parse the command line arguments.
        
        This function uses the arguments passed in through :meth:`arguments`,
        adds the `-h` option, and calls the parser to understand and act on 
        the arguments. Arguments are then stored in the :attr:`opts` attribute.
        
        This method also calls :meth:`configure_logging` to set up the logger
        if it is ready to go.
        
        .. note:: 
            Calling :meth:`configure_logging` allows :meth:`configure` to 
            change the logging configuration values before the logger is 
            configured.
        
        """
        self._add_help()
        self._opts = self.parser.parse_args(self._rargs, self._opts)
        self.configure_logging()
        
    @abc.abstractmethod
    def do(self): # pylint: disable= invalid-name
        """This method should handle the main operations for the command 
        line tool. The user should overwrite this method in Engine subclasses
        for thier own use. The :exc:`KeyboardInterrupt` or :exc:`SystemExit` 
        errors will be caught by :meth:`kill`"""
        pass
        
    def kill(self):
        """This function should forcibly kill any subprocesses. It is called 
        when :meth:`do` raises a :exc:`KeyboardInterrupt` or :exc:`SystemExit`
        to ensure that any tasks can be finalized before the system exits.
        Errors raised here are not caught."""
        pass
            
    def run(self):
        """This method is used to run the command line engine in the expected 
        order. This method should be called to run the engine from another 
        program."""
        if not self._hasinit:
            self.init()
        if not self._hasargs:
            warn("Implied Command-line mode", UserWarning)
            self.arguments()
        self.before_configure()
        self.configure()
        self.after_configure()
        self.parse()
        try:
            self.do()
        except SystemExit as exc:
            if not getattr(exc, 'code', 0):
                self.kill()
            if self.debug:
                raise
            self.exitcode = getattr(exc, 'code', self.exitcode)
        except KeyboardInterrupt as exc:
            self.kill()
            if self.debug:
                raise
        return self.exitcode
    
    @classmethod        
    def script(cls):
        """The class method for using this module as a script entry 
        point. This method ensures that the engine runs correctly on 
        the command line, and is cleaned up at the end."""
        engine = cls()
        engine.arguments()
        return engine.run()
        
    def _remove_help(self):
        """Remove the ``-h, --help`` argument from the parser.
        
        .. Warning::
            This method uses a swizzle to access protected parser attributes
            and remove the argument as best as possible. It may break!
        """
        # pylint: disable= protected-access
        for option_string in self.__help_action.option_strings:
            del self._parser._option_string_actions[option_string]
        self._parser._remove_action(self.__help_action)
    
    def _add_help(self):
        """Add the ``-h, --help`` argument."""
        self.__help_action = self.parser.add_argument('-h', '--help',
            action='help', help="Display this help text")
            
    def _add_configfile_args(self,*args):
        """Add a parser command line argument for changing configuration files.
        
        :arguments: The set of arguments to be passed to :meth:`~argparse.ArgumentParser.add_argument`.
        
        """
        if len(args) == 0:
            args = ("--config",)
        self.parser.add_argument(*args, dest='config',
            action='store', metavar='file.yml', default=self.defaultcfg,
            help="Set configuration file. By default, load %(file)s and"
            " ~/%(file)s if it exists." % dict(file=self.defaultcfg))
        self.parser.register('action', 'config', bind_configuration_action(self.config))
            
    def _add_configure_args(self,*args):
        """Add a parser command line argument for literal configuration items.
        
        See :meth:`~pyshell.config.DottedConfiguration.parse_literals`.
        
        :arguments: The set of arguments to be passed to :meth:`~argparse.ArgumentParser.add_argument`.
        
        """
        if len(args) == 0:
            args = ("--configure",)
        self.parser.add_argument(*args, dest='configure',
            action='append', metavar='Item.Key=value',default=[],
            help="Set configuration value. The value is parsed as a"
            " python literal.")
    
    def configure_logging(self):
        """Configure the logging system using the configuration underneath 
        ``config["logging"]`` as a dictionary configuration for the :mod:`logging` 
        module."""
        configure_logging(self.config)
        