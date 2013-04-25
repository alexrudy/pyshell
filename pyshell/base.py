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

Using :class:`CLIEngine` for Command Line Interfaces
====================================================

The :class:`CLIEngine` is designed with "Convention over Configuration"
in mind. That is, it aims to set everything up so that it will work out
-of-the-box, and the user is responsbile for adjusting undesireable
behavior. Basically, all you have to do is write a subclass of
:class:`CLIEngine` with only a :meth:`~CLIEngine.do` method (no need for
:meth:`__init__`!). See :ref:`cliengine_examples` for examples.

Writing your own Subclass
-------------------------
    
This class should be subclassed by the user, who should re-implement 
the following methods:
    
- :meth:`~CLIEngine.do`  - Does the 'real work'.
- :meth:`~CLIEngine.kill` - Called if the engine tries to exit abnormally.
    
These funcitons are used in the normal operation of the command line engine.
    
The user should also override the desired instance variables on the class.
Useful instance variables to consider overriding are 
:attr:`~CLIEngine.defaultcfg` and :attr:`~CLIEngine.description`

Other methods are used to control the engine during normal operation. These 
methods should in general not be overwritten, but can be modified in 
subclasses, so long as they are called using the 
``super(ClassName, self).method()`` construct.
    
Running your subclass
---------------------

To run the engine, use :meth:`~CLIEngine.run`. To run the engine without 
instantiating the class, use :meth:`~CLIEngine.script`, a class method 
that instantiates a new object, and runs the tool. Both methods 
accomplish the same thing at the end of the day.

You can use :meth:`~CLIEngine.script` to start the engine with the "if main" 
python convention ::

    if __name__ == '__main__':
        Engine.script()

Using :meth:`~CLIEngine.script` allows the developer to set this as
an entry point in their ``setup.py`` file, and so provide the command
line enegine as a command line tool in a distutils supported python package.
A basic entry point for this tool would appear like ::
    
    ["PyScript = mymodule.cli:Engine.script"]
    

How :class:`CLIEngine` works
----------------------------

The engine is set up to use a configuration file system, 
provide basic parsing attributes, and an interruptable 
command line interaction flow. The configuration is designed 
to provide dynamic output and to configure the system 
before it completes the parsing process.

1.  Initialization loads the object, and sets up the argument parser. 
    At this point, parser should only understand arguments that are neeeded 
    to print the best `--help` message.

2.  Preliminary Arguments are parsed by :meth:`arguments`.

3.  Configuration is handled by the :meth:`configure` function. This 
    function loads the following configuration files in order (such that the 
    last one loaded is the one that takes precedence):

    *   The ``defaultcfg`` file from ``engine.__module__``. This allows the 
        developer to provide a base configuration for the engine.

    *   The requested configuration file from the user's home directory.

    *   The requested configuration file form the current directory.

    *   If no configuration file is requested, the filename for `defaultcfg` 
        will be used. As well, if the engine cannot find the requested 
        configureation file in the current directory (i.e. the user asks for 
        a file, and it isn't there) a warning will be issued.

4.  Help message is inserted into parsing, and remining arguments
    parsed by :meth:`parse`. At this point, the entire configuration process
    is complete.

5.  The function :meth:`do` is called, This should do the bulk of the engine's
    work.

6.  If the user interrupts the operation of the program, :meth:`kill` will
    be called. If python is in ``__debug__`` mode, this will raise a full
    traceback. If not, the traceback will be suppressed.


Reference for :class:`CLIEngine`, the Command Line Interface Engine
-------------------------------------------------------------------

.. autoclass::
    CLIEngine
    :members:
    :private-members:
    

Call structure of :meth:`run`
-----------------------------
The call structure of the method :meth:`~CLIEngine.run`, the main script driver.
This is provided as a reference. Note that the :meth:`~CLIEngine.init` is called
during :meth:`~CLIEngine.arguments` when :meth:`~CLIEngine.arguments` is called
outside of :meth:`~CLIEngine.run`, allowing you to use the following sequence to
run a subclass of :class:`CLIEngine`::
    
    CLIInstance = CLIEngine()
    CLIInstance.arguments("--faked CLI --arguments".split())
    CLIInstance.run()
    

.. literalinclude:: ../pyshell/base.py
    :linenos:
    :pyobject: CLIEngine.run



"""
from __future__ import print_function, unicode_literals, division

from argparse import ArgumentParser, RawDescriptionHelpFormatter
import os, os.path
import abc
from warnings import warn
from .config import StructuredConfiguration as Config, Configuration as BConfig
from .util import semiabstractmethod, deprecatedmethod
import logging, logging.config

__all__ = [ 'CLIEngine',
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

class CLIEngine(object):
    """A base class for Command Line Inteface facing tools. :class:`CLIEnigne` 
    provides the basic structure to set up a simple command-line interface,
    based on the :mod:`argparse` framework.
    
    :param str prefix_chars: Sets the prefix characters to command line arguments. 
        by default this is set to "-", reqiuring that all command line argumetns begin 
        with "-".
    
    At the end of initialization, the configuration (:attr:`config`) and 
    :attr:`parser` will be availabe for use.
    """
    # pylint: disable= too-many-instance-attributes
    
    __metaclass__ = abc.ABCMeta
    
    @property
    def description(self):
        """The textual description of the command line interface, 
        set as the description of the parser from :mod:`argparse`."""
        return self.__doc__
        
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
    in the current direction, use ``__main__`` as the module name."""
    
    def __init__(self, prefix_chars="-".encode('utf-8'), 
        conflict_handler='error'):
        super(CLIEngine, self).__init__()
        self._log = logging.getLogger(self.__module__)
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
        self.__help_action = None
        self.exitcode = 0
        self._hasinit = False
        self._hasargs = False
        self._hasvars = True
        
        
    @property
    def parser(self):
        """:class:`argparse.ArgumentParser` instance for this engine."""
        if getattr(self, '_hasvars', False):
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
        
    @deprecatedmethod(version="0.3",replacement=".do()")
    @semiabstractmethod("Method .start() will be deprecated after version 0.3")
    def start(self):
        """This function is called at the start of the :class:`CLIEngine` 
        operation. It should contain any process spawning that needs to 
        occur.
        
        .. deprecated:: 0.2
            Use :meth:`do` instead.
        """
        pass
        
    
    def do(self): # pylint: disable= invalid-name
        """This method should handle the main operations for the command 
        line tool. The user should overwrite this method in Engine subclasses
        for thier own use. The :exc:`KeyboardInterrupt` or :exc:`SystemExit` 
        errors will be caught by :meth:`kill`"""
        try:
            self.start()
            self.end()
        except NotImplementedError:
            raise NotImplementedError("Command line tools must overwrite the"
            " method do() with their desired actions.")
        
    @deprecatedmethod(version="0.3",replacement=".do()")
    @semiabstractmethod("Method .end() will be deprecated after version 0.3")
    def end(self):
        """This function is called at the end of the :class:`CLIEngine` 
        operation and should ensure that all subprocesses have ended.
        
        .. deprecated:: 0.2
            Use :meth:`do` instead.
        """
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
            if __debug__:
                raise
            self.exitcode = getattr(exc, 'code', self.exitcode)
        except KeyboardInterrupt as exc:
            self.kill()
            if __debug__:
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
        if "logging" in self.config:
            logging.config.dictConfig(self.config["logging"])
            if "py.warnings" in self.config["logging.loggers"]:
                logging.captureWarnings(True)
        