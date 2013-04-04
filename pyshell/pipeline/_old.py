# -*- coding: utf-8 -*-
# 
#  pipeline.py
#  pyshell
#  
#  Created by Alexander Rudy on 2012-11-21.
#  Copyright 2012 Alexander Rudy. All rights reserved.
# 
from __future__ import division
from datetime import datetime

from .base import CLIEngine
from .util import func_lineno

import argparse
import re
import logging

import ipdb

__version__ = "0.1"

class PipelineException(Exception):
    """Exceptions in Pipelines"""
        
class PipelineStateException(PipelineException):
    """Exceptions in Pipeline State"""
        

class Pipe(object):
    """A single component of a pipeline"""
    def __init__(self,name,action,description,exceptions,dependencies,replaces,optional,triggers):
        super(Pipe, self).__init__()
        self.name = name
        self.action = action
        if self.action is None:
            self.action = lambda : None
        self.exceptions = exceptions
        self.dependencies = dependencies
        self.replaces = replaces
        self.optional = optional
        self.description = description
        self.triggers = triggers
        
        # Setup Flags
        self.queued = False
        self.replaced = False
        
        # Operational Flags
        self.ran = False
        self.complete = False
        self.satisfied = False
        
    def run(self):
        """Run the pipe"""
        try:
            self.time_start = datetime.now()
            self.ran = True
            self.action()
        except:
            raise
        else:
            self.complete = True
        finally:
            self.time_end = datetime.now()
            self.time_dur = self.time_end - self.time_start
            
class Pipeline(CLIEngine):
    """An object for managing a collection of pipes, and building that collection based on class functions"""
    def __init__(self, name="__class__.__name__"):
        self.name = name        
        if name == "__class__.__name__":
            self.name = self.__class__.__name__
        if isinstance(name,str):
            self.name = self.name.encode('utf-8')
        
        super(Pipeline, self).__init__(prefix_chars='+-')
        
        self.pipes = {}
        self.macros = {}
        self.functions = {}
        self.exclude = []
        self.include = []
        self.trigger = []
        self.orders = []
        self.execution = []
        self.execution_code = []
        self.execution_level = []

        self.attempt = [] # Pipes and dependents which have been attempted.        
        self.complete = [] # Pipes and dependents which have been walked
        self.done = [] # Pipes and dependents which have been checked
        self.ran = [] # Pipes and dependents which have been executed
        self.aran = []
        self.order = None
        
        # The following are boolean state values for the pipeline
        self._reset()
        self._pipe_tree = []
        
        self.log = logging.getLogger(self.module)
        logging.addLevelName(25,'STATUS')
        
        self.version = [self.name + u": " + __version__]
        
        self._initOptions()
    
    @property
    def description(self):
        HelpDict = { 'command': u"%(prog)s",'name': self.name }
        ShortHelp = u"""
        Command Line Interface for %(name)s.
        The pipeline is set up in pipes, which are listed below. 
        By default, the *all pipe should run the important parts of the pipeline.
        
        (+) Include      : To include a pipe, use +pipe. This will also run the dependents for that pipe.
        (-) Exclude      : To exclude a pipe, use -pipe. 
        
        To run the simulater, use 
        $ %(command)s *all""" % HelpDict
        return ShortHelp
        
    @property
    def epilog(self):
        return u"""This is a multi-function dynamic command line interface to a complex program. 
The base unit, pipes, are individual functions which should be able to run independtly of each other. 
Pipes can declare dependencies if they are not independent of each other. The command line interface
can be customized using the 'Default' configuration variable in the configuration file.
        """
            
    def _reset(self):
        """Re-set flag variables to initial states."""
        self.configured = False
        self.running = False
        self.plotting = False
        self.debugging = False
        self.caching = True
        self.starting = False
        self.started = False
        self.paused = False
        self.progressbar = False
        
        
    def _initOptions(self):
        """Initializes the command line options for this script. This function is automatically called on construction, and provides the following default command options which are already supported by the pipeline:
        
        Command line options are:
        
        =========================================== =====================
        CLI Option                                  Description
        =========================================== =====================
        ``--version``                               Display version information about this module
        ``--configure Option.Key=Value``            Set a configuration value on the command line. 
        ``-c file.yaml, --config-file file.yaml``   Specify a configuration file
        ``-n, --dry-run``                           Print the pipes this command would have run.
        ``--show-tree``                             Show a dependency tree for the simulation
        ``--show-pipes``                           List all of the used pipes for the simulation
        ``--dump-config``                           Write the current configuration to file
        ``--list-pipes``                           Print the pipes that the command will execute, do not do anything
        =========================================== =====================
        
        Macros defined at this level are:
        
        ========= ==================================================
        Macro     Result
        ========= ==================================================
        ``*all``   Includes every pipe
        ``*none``  Doesn't include any pipes (technically redundant)
        ========= ==================================================
        
        """
        # Parsers
        self.config_parser = self._parser.add_argument_group("configuration presets")
        self.cache_parser = self._parser.add_argument_group("caching control")
        self.pos_pipe_parser = self._parser.add_argument_group('Single Use Pipes')
        self.neg_pipe_parser = self._parser.add_argument_group('Remove Pipes')
        
        # Add the basic controls for the script
        self._parser.add_argument('--version',action='version',version="\n".join(self.version))
        
        # Operational Controls
        self.registerConfigOpts('d',{'Debug':True},help="enable debugging messages and plots")
        
        # Config Commands
        self._parser.add_argument('--configure',action='append',metavar="Option.Key='literal value'",help="add configuration items in the form of dotted names and value pairs: Option.Key='literal value' will set config[\"Option.Key\"] = 'literal value'",dest='literalconfig')
        
        self.registerFunction('-n','--dry-run', self.dry_run, run='post',help="run the simulation, but do not execute pipes.")
        self.registerFunction('--show-tree', self.pipe_tree, run='end',help="show a dependcy tree of all pipes run.")  
        self.registerFunction('--list-pipes', self.pipe_list, run='end', help="show a list of all pipes.")
        
        # Default Macro
        self.registerPipe(None,"all",description="Run all pipes",help="Run all pipes",include=False)
        self.registerPipe(None,"none",description="Run no pipes",help="Run no pipes",include=False)
        
    #########################
    ### REGISTRATION APIs ###
    #########################    
        
    def registerPipe(self,action,name=None,
        description=None,exceptions=None,include=None,help=False,dependencies=None,replaces=None,optional=False,triggers=None):
        """Register a pipe for operation with the pipeline. The pipe will then be available as a command line option, and will be operated with the pipeline. Pipes should be registered early in the operation of the pipeline (preferably in the initialization, after the pipeline class itself has initialized) so that the program is aware of the pipes for running. 
        
        :keyword function pipe: The function to run for this pipe. Should not take any arguments
        :keyword string name:  The command-line name of this pipe (no spaces, `+`, `-`, or `*`)
        :keyword string description: A short description, which will be used by the logger when displaying information about the pipe
        :keyword tuple exceptions: A tuple of exceptions which are acceptable results for this pipe. These exceptions will be caught and logged, but will allow the pipeline to continue. These exceptions will still raise errors in Debug mode.
        :keyword bool include: A boolean, Whether to include this pipe in the `*all` macro or not.
        :keyword string help: Help text for the command line argument. A value of False excludes the help, None includes generic help.
        :keyword list dependencies: An ordered list of the pipes which must run before this pipe can run. Dependencies will be deep-searched.
        :keyword list replaces: A list of pipes which can be replaced by this pipe. This pipe will now satisfy those dependencies.
        :keyword bool optional: A boolean about wheather this pipe can be skipped. If so, warnings will not be raised when this pipe is explicitly skipped (like ``-pipe`` would do)
        
        
    	Pipes are called with either a ``*``, ``+`` or ``-`` character at the beginning. Their resepctive actions are shown below.
	
    	========= ============ ================================
    	Character  Action      Description
    	========= ============ ================================
    	``*``     Include      To include a pipe, use ``*pipe``. This will also run the dependents for that pipe.
    	``-``     Exclude      To exclude a pipe, use ``-pipe``. This pipe (and it's dependents) will be skipped.
    	``+``     Include-only To include a pipe, but not the dependents of that pipe, use ``+pipe``.
    	========= ============ ================================
        
        Pipes cannot be added dynamically. Once the pipeline starts running (i.e. processing pipes) the order and settings are fixed. Attempting to adjsut the pipes at this point will raise an error.
        """
        if self.running or self.starting:
            raise PipelineStateException("Cannot add a new pipe to the pipeline, the simulation has already started!")
        if name == None:
            name = action.__name__
        name = name.replace("_","-")
            
        if name in self.pipes:
            raise PipelineException("Cannot have duplicate pipe named %s" % name)
        
        if hasattr(action,'optional'):
            optional = action.optional
        
        if exceptions == None and hasattr(action,'exceptions'):
            exceptions = action.exceptions
        elif exceptions == None:
            exceptions = tuple()
        if exceptions == True:
            exceptions = Exception
        
        if triggers == None and hasattr(action,'triggers'):
            triggers = action.triggers
        elif triggers == None:
            triggers = []
        if not isinstance(triggers,list):
            raise ValueError("Invalid type for triggers: %s" % type(triggers))
        
        if dependencies == None and hasattr(action,'dependencies'):
            dependencies = action.dependencies
        elif dependencies == None:
            dependencies = []
        if not isinstance(dependencies,list):
            raise ValueError("Invalid type for dependencies: %s" % type(dependencies))
            
        if replaces == None and hasattr(action,'replaces'):
            replaces = action.replaces  
        elif replaces == None:
            replaces = []
        if not isinstance(replaces,list):
            raise ValueError("Invalid type for dependencies: %s" % type(replaces))
        
        if description == None and hasattr(action,'description'):
            description = action.description
        elif description == None and callable(action):
            description = action.__doc__
        elif not description:
            description = "Running %s" % name

        if (not help) and hasattr(action,'help'):
            help = action.help
        elif help == False:
            help = argparse.SUPPRESS
        elif help == None:
            help = "pipe %s" % name

        if include == None and hasattr(action,'include'):
            include = action.include
        elif include == None:
            include = False    
        
        pipe = Pipe(action=action,name=name,description=description,exceptions=exceptions,
            dependencies=dependencies,replaces=replaces,optional=optional,triggers=triggers)
        self.pipes[name] = pipe
        self.orders += [name]
        self.pos_pipe_parser.add_argument("+"+name,action='append_const',dest='include',const=name,help=help)
        self.neg_pipe_parser.add_argument("-"+name,action='append_const',dest='exclude',const=name,help=argparse.SUPPRESS)
        if include:
            self.pipes["all"].dependencies += [name]
        
    def registerFunction(self,*arguments,**kwargs):
        """Register a function to run using a flag.
        
        :param string argument: The calling argument, e.g. ``--hello-world``. Multiple arguments can be provided.
        :param function function: The function to be run. This should be the last comma separated argument.
        :keyword str help: Command line help for this function.
        :keyword str run: ('pre'|'post'|'end') Whether to run the function before or after configuration of the pipeline, or at the end of the simulation.
        :keyword str name: An explicit function name.
        
        Functions registered with ``post=False`` will be run before the pipeline is configured from a file. As such, changes they make can be easily re-adjusted by the user. Functions registered with ``post=True`` (the default) will run after configuration, but before any pipes run. They can be used to inspect or adjust configuration variables or other globals.
        
        Other keyword arguments are passed to :meth:`ArgumentParser.add_argument`
        """
        
        help = kwargs.pop("help",argparse.SUPPRESS)
            
        run = kwargs.pop('run','post')
        runOpts = { 'post' : 'afterFunction' , 'pre' : 'beforeFunction', 'end' : 'endFunction'}
        if run not in runOpts:
            raise KeyError("Run option not supported: %s, %s" % (run,runOpts.keys()))
        
        arguments = list(arguments)
        function = arguments.pop()
        
        name = kwargs.pop('name',function.__name__)
        
        self.functions[name] = function
        
        if len(arguments) < 1 and not self.running:
            self.config["Options"].update({ runOpts[run] : [name] })
        elif not self.running and not self.starting:
            self._parser.add_argument(*arguments,action='append_const',dest=runOpts[run],const=name,help=help,**kwargs)
        else:         
            raise PipelineStateException("Cannot add function after pipeline has started!")
            
        
    def registerConfigOpts(self,argument,configuration,preconfig=True,**kwargs):
        """Registers a bulk configuration option which will be provided with the USAGE statement. This configuration option can easily override normal configuration settings. Configuration provided here will override programmatically specified configuration options. It will not override configuration provided by the configuration file. These configuration options are meant to provide alterantive *defaults*, not alternative configurations.
        
        :param string argument: The command line argument (e.g. ``-D``)
        :param dict configuration: The configuration dictionary to be merged with the master configuration.
        :keyword bool preconfig: Applies these adjustments before loading the configuration file.
        
        Other keyword arguments are passed to :meth:`ArgumentParser.add_argument`
        """
        if self.running or self.starting:
            raise PipelineStateError("Cannot add macro after pipeline has started!")
        
        if "help" not in kwargs:
            help = argparse.SUPPRESS
        else:
            help = kwargs["help"]
            del kwargs["help"]
                
        if preconfig:
            dest = 'beforeConfigure'
        else:
            dest = 'afterConfigure'
            
        self.config_parser.add_argument("-"+argument,action='append_const',dest=dest,const=configuration,help=help,**kwargs)
        
    
    def collect(self, matching=r'^(?!\_)', genericClasses=(), **kwargs):
        """Collect class methods for inclusion as pipeline pipes. Instance methods are collected if they do not belong to the parent :class:`Pipeline` class (i.e. this method, and others like :meth:`registerPipe` will not be collected.). Registered pipes will default to having no dependents, to be named similar to thier own methods (``collected_pipe`` becomes ``*collected-pipe`` on the command line) and will use thier doc-string as the pipe description. The way in which these pipes are collected can be adjusted using the decorators provided in this module.
        
        To define a method as a pipe with a dependent, help string, and by default inclusion, use::
            
            @collect
            @include
            @description("Doing something")
            @help("Do something")
            @depends("other-pipe")
            @replaces("missing-pipe")
            def pipename(self):
                pass
        
        This method does not do any logging. It should be called before the :meth:`run` method for the pipeline is called.
        
        Private methods are not included using the default matching string ``r'^(?!\_)'``. This string excludes any method beginning with an underscore. Alternative method name matching strings can be provided by the user.
        
        :param string matching: Regular expression used for matching method names.
        :param kwargs: Keyword arguments passed to the :meth:`registerPipe` function.
        
        """
        genericList = dir(Pipeline)
        for gClass in genericClasses:
            genericList += dir(gClass)
        currentList = dir(self)
        pipeList = []
        for methodname in currentList:
            if (methodname not in genericList):
                method = getattr(self,methodname)
                if callable(method) and ( re.search(matching,methodname) or getattr(method,'collect',False) ) and ( not getattr(method,'ignore',False) ):
                    pipeList.append(method)
                    
        pipeList.sort(key=func_lineno)
        [ self.registerPipe(pipe,**kwargs) for pipe in pipeList ]
    
    
    def configure(self):
        """Configuration before final arguments are placed into methods"""
        for fk in self.config.get("Options.beforeFunction",[]):
            self.functions[fk]()
        for cfg in self.config.get("Options.beforeConfigure",[]):
            self.config.merge(cfg)
        super(Pipeline, self).configure()
        opts_dict = vars(self.opts)
        for key in opts_dict.keys():
            if opts_dict[key] == None:
                del opts_dict[key]
        self.config["Options"].merge(opts_dict)
        self.orders.remove("all")
        self.orders += ["all"]
        
    
    def start(self):
        """Start up the simulation. This function handles the configuration of the system, and prepares for any calls made to :meth:`do`."""
        self.starting = True
        if not isinstance(self.config.get("Options.exclude",False),list):
            self.config["Options.exclude"] = []
        if not isinstance(self.config.get("Options.include",False),list):
            self.config["Options.include"] = []
        
        # Handler command line literal configurations.
        for item in self.config.get("Options.literalconfig",[]):    
            key,value = item.split("=")
            try:
                self.config[key] = literal_eval(value)
            except:
                self.config[key] = value
        
        # Handle post configuration updates
        for cfg in self.config.get("Options.afterConfigure",[]):
            self.config.merge(cfg)
        
        
        for fk in self.config.get("Options.afterFunction",[]):
            self.functions[fk]()
            


        self.starting = False
        self.started = True
        
    def do(self,*pipes):
        """Run the simulator.
        
        :argument pipes: Pipes to be run as macros.
        
        This command can be used to run specific pipes and their dependents. The control is far less flow control than the command-line interface (there is currently no argument interface to inclusion and exclusion lists, ``+`` and ``-``.), but can be used to call single macros in simulators froms scripts. In these cases, it is often beneficial to set up your own macro (calling :func:`registerPipe` with ``None`` as the pipe action) to wrap the actions you want taken in each phase.
        
        It is possible to stop execution in the middle of this function. Simply raise an :exc:`PipelinePause` exception and the simulator will return, and remain in a state where you are free to call :meth:`do` again."""
        if not self.started:
            raise PipelineStateException("Pipeline has not yet started!")
        elif self.running:
            raise PipelineStateException(u"Pipeline is already running!")
        self.running = True
        self.include = []
        self.include += list(pipes)
        self.include += self.config["Options.include"]
        if self.attempt == []:
            self.inorder = True
            self.complete = []
        if len(self.include) == 0 and self.config.get("Default",None) is not None:
            self.include += self.config.get("Default",[])
        if len(self.include) == 0:
            self.parser.error(u"No pipes triggered to run!")
        self.trigger = []
        self.pipe_order()
        print("Registered Pipes:")
        for i in range(len(self.execution)):
            print (" " * self.execution_level[i]) + (self.symbols[self.execution_code[i]] % self.execution[i])
        print("Execution Order:")
        execute = []
        for i in range(len(self.execution)):
            if self.execution_code[i] in self.called:
                execute.append(self.execution[i])
        execute.reverse()
        print execute
        pipe,code = self.next_pipe(None,dependencies=True)
        while code != "F":
            self.execute(pipe,code=code)
            pipe,code = self.next_pipe(None,dependencies=True)
        self.running = False
        return self.complete
    
    codes = {
        'I' : "Included, Called",
        'Id' : "Included, Satisfied",
        'D' : "Dependency, Called",
        'Dd' : "Dependency, Satisfied",
        'T' : "Triggered, Called",
        'Td' : "Triggered, Satisfied",
        "Rd" : "Replaces, Satisfied"
    }
    called = {
        'I' : "Id",
        'D' : "Dd",
        'T' : "Td"
    }
    symbols = {
        'T' : u"┌>%s",
        'I' : u"+>%s",
        'D' : u"└>%s",
        'Id' :u"- %s",
        'Dd' :u"└ %s",
        'Td' :u"┌ %s",
        'Rd' :u"x %s",
    }
    
    
    def pipe_order(self):
        """Return the name of the next pipe"""
        self.orders.reverse()
        for pipe in self.orders:
            if pipe in self.include:
                # ipdb.set_trace()
                self._next_pipe("I",pipe,0)
            
    def _next_pipe(self,code,pipe,level):
        """docstring for _next_pipe"""
        if pipe in self.execution:
            self.execution += [pipe]
            self.execution_code += [self.called.get(code,code)]
            self.execution_level += [level]
        else:
            for t in self.orders:
                if t in self.pipes[pipe].triggers:
                    self._next_pipe("T",t,level=level+1)
            self.execution += [pipe]
            self.execution_code += [code]
            self.execution_level += [level]
            for r in self.orders:
                if r in self.pipes[pipe].replaces:
                    self._next_pipe("Rd",r,level=level+1)
            for d in self.orders:
                if d in self.pipes[pipe].dependencies:
                    self._next_pipe("D",d,level=level+1)
        
        
                    
                    
    
    def execute(self,pipe,level=0,code=""):
        """Actually exectue a particular pipe. This function can be called to execute individual pipes, either with or without dependencies. As such, it gives finer granularity than :func:`do`.
        
        :param string pipe: The pipe name to be exectued.
        :param bool dependencies: Whether to run all dependencies.
        
        This method handles exceptions from the called pipes, including keyboard interrupts.
        """
        if self.paused or not self.running:
            return False
            
        if pipe not in self.pipes:
            self.log.critical("Pipe %s does not exist." % pipe)
            self.exit(1)
        use = True
        if pipe in self.trigger:
            use = True
        if pipe in self.config["Options.exclude"]:
            use = False
        if pipe in self.config["Options.include"]:
            use = True
        if pipe in self.attempt:
            return use
        if pipe in self.complete:
            return use
        if not use:
            return use
        
        self.attempt += [pipe]
        if code == "T":
            indicator = u"->%s"
            level = 0
        elif code == "I":
            indicator = u"+>%s"
            level = 0
        elif code == "C":
            indicator = u"=>%s"
        elif code == "D":
            indicator = u"└>%s"
        elif code == "M":
            indicator = u"*>%s"
        else:
            indicator = u"  %s"
        for dependent in self.orders:
            if dependent in self.pipes[pipe].dependencies:
                if dependent not in self.attempt and dependent not in self.complete:
                    self.execute(dependent,level=level+1,code="D")
                else:
                    self._pipe_tree += ["%-30s : (done already)" % (u"  " * (level+1) + u"└ %s" % dependent)]
        
        for dependent in self.pipes[pipe].dependencies:
            if dependent not in self.orders:
                self.log.error("Pipe %r requested dependent %r which doesn't exist." % (pipe, dependent))
                raise PipelineStateError("Pipe %r requested dependent %r which doesn't exist." % (pipe, dependent))
            elif dependent not in self.complete and self.pipes[dependent].optional:
                self.log.debug(u"Pipe %r requested by %r but skipped" % (dependent,pipe))
            elif dependent not in self.complete:
                self.log.warning(u"Pipe '%s' required by '%s' but failed to complete." % (dependent,pipe))
            
        
        
        s = self.pipes[pipe]
        self._pipe_tree += [u"%-30s : %s" % (u"  " * level + indicator % pipe,s.description)]
        if self.config.get("Options.DryRun",False):
            self.trigger += self.pipes[pipe].triggers
            self.complete += [pipe] + s.replaces
            self.done += [pipe]
            return use
        elif pipe in self.complete:
            return use
        
        self.log.log(25,u"%s" % s.description)
        if s.optional:
            s.exceptions = Exception
        
        try:
            s.run()
        except (KeyboardInterrupt,SystemExit) as e:
            self.log.critical(u"Keyboard Interrupt during %(pipe)s... ending simulator." % {'pipe':s.name})
            self.log.critical(u"Last completed pipe: %(pipe)s" % {'pipe':self.complete.pop()})
            self.log.debug(u"Pipes completed: %s" % ", ".join(self.complete))
            raise
        except s.exceptions as e:
            emsgA = u"Error %(name)s in pipe %(pipe)s:%(desc)s. Pipe indicated that this error was not critical" % {'name': e.__class__.__name__, 'desc': s.description,'pipe':s.name}
            emsgB = u"Error: %(msg)s" % {'msg':e}
            if s.optional:
                self.log.debug(emsgA)
                self.log.debug(emsgB)
            else:
                self.log.error(emsgA)
                self.log.error(emsgB)
                if self.config["Debug"]:
                    raise
        except Exception as e:
            self.log.critical(u"Error %(name)s in pipe %(pipe)s:'%(desc)s'!" % { 'name' : e.__class__.__name__, 'desc' : s.description, 'pipe' : s.name } )
            self.log.critical(u"Error: %(msg)s" % { 'msg' : e } )
            raise
        else:
            self.log.debug(u"Completed '%s' and %r" % (s.name,s.replaces))
            self.trigger += self.pipes[pipe].triggers
            self.complete += [pipe] + s.replaces
            self.ran += [pipe]
            self.done += [pipe]
        finally:
            self.aran += [pipe]
            self.log.debug(u"Finalized '%s'" % s.name)
        
        return use
        
    def end(self,code=0,msg=None):
        """This function exist the current python instance with the requested code. Before exiting, a message is printed.
        
        :param int code: exit code
        :param string msg: exit message
        
        """
        for fk in self.config.get("Options.endFunction",[]):
            self.functions[fk]()
        if msg:
            self.log.info(msg)
        self._reset()
        if code != 0 and self.commandLine:
            self.log.critical("Pipeline exiting abnormally: %d" % code)
            sys.exit(code)
        elif code != 0:
            self.log.critical("Pipeline closing out, exit code %d" % code)
        else:
            self.log.info(u"Pipeline %s Finished" % self.name)
            
    def pipe_tree(self):
        """Displays the pipe tree."""
        self._pipe_tree.reverse()
        text = u"Dependency Tree, request order:\n"
        text += "\n".join(self._pipe_tree)
        self.log.log(25,text)
        
    def pipe_list(self):
        """A list of all available pipes and their descriptions."""
        text = [u"Pipes loaded in %s" % self]
        for pipe in self.orders:
            p = self.pipes[pipe]
            text += [u"%s : %s" % (p.name,p.description)]
        self.log.log(25,"\n".join(text))
        
    def dry_run(self):
        """Flip the simulator into dry-run mode."""
        self.config.setdefault("Options.DryRun",True)
    