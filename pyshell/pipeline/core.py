# -*- coding: utf-8 -*-
# 
#  pipeline2.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-03-16.
#  Copyright 2013 Alexander Rudy. All rights reserved.
# 
"""
.. autoclass:: Pipeline
    :members:
    :inherited-members:

"""
import time
import argparse
import re
import logging
from collections import OrderedDict

from .. import CLIEngine
from ..core import Stateful, State, Typedkwargs
from .pipe import Pipe
from .profile import Profile
from ..util import func_lineno, ipydb

ipydb()


class PipelineException(Exception):
    """Exceptions in Pipelines"""
        
class PipelineStateException(PipelineException):
    """Exceptions in Pipeline State"""
        
        
class Pipeline(CLIEngine,Stateful):
    """docstring for Pipeline"""
    def __init__(self):
        super(Pipeline, self).__init__(prefix_chars="-+")
        self.pipes = OrderedDict()
        self._state = State.fromkeys(["initialized","configured","parsed","started","running","paused","finished"],False)
        self.version = ["0.0"]
        
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
    
    @property
    def name(self):
        """Return the name of this simulator"""
        if isinstance(getattr(self,'_name',None),unicode):
            return self._name
        else:
            return self.__class__.__name__.encode("utf-8")
            
    
    def pipes_with_state(self,*states):
        """Return the pipes with a specific state set."""
        result = set()
        for state in states:
             result.update([ pipe.name for pipe in self.pipes.values() if pipe.state[state] ])
        return list(result)
    
    @property
    def attempted(self):
        """A list of pipes that have been attempted to run"""
        return self.pipes_with_state("started")
        
    @property
    def completed(self):
        """A list of completed pipes"""
        return self.pipes_with_state("completed")
        
    def init(self):
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
        ``--show-pipes``                            List all of the used pipes for the simulation
        ``--dump-config``                           Write the current configuration to file
        ``-p, --profile``                           Write a profile to an HTML file.
        =========================================== =====================
        
        Macros defined at this level are:
        
        ========= ==================================================
        Macro     Result
        ========= ==================================================
        ``+all``   Includes every pipe
        ``+none``  Doesn't include any pipes (technically redundant)
        ========= ==================================================
        
        """
        super(Pipeline, self).init()
        
        # Parsers
        self.config_parser = self.parser.add_argument_group("Configuration presets")
        self.pos_pipe_parser = self.parser.add_argument_group('Add Pipes')
        self.neg_pipe_parser = self.parser.add_argument_group('Remove Pipes')
        
        # Add the basic controls for the script
        self.parser.add_argument('--version',action='version',version="\n".join(self.version))
                
        # Config Commands
        self.register_config({"System":{"DryRun":True}},'-n','--dry-run', help="run the simulation, but do not execute pipes.")
        self.register_config({"Actions":{"ShowTree":True}},'--show-tree', help="show a dependcy tree of all pipes run.")
        self.register_config({"Actions":{"ListPipe":True}},'--show-pipes', help="show a list of all pipes.")
        self.register_config({"Actions":{"Profile":True}},'-p','--profile', help="output a profile to a file 'profile.html'")
        
        # Default Macro
        self.register_pipe(lambda : None,name="all",description="Run all pipes",help="Run all pipes",include=False)
        self.register_pipe(lambda : None,name="none",description="Run no pipes",help="Run no pipes",include=False)
        
        self.set_state("initialized")
        
    def register_pipe(self,action,**kwargs):
        """Register a pipe for operation with the pipeline. The pipe will then be available as a command line option, and will be operated with the pipeline. Pipes should be registered early in the operation of the pipeline (preferably in the initialization, after the pipeline class itself has initialized) so that the program is aware of the pipes for running. 
        
        :keyword action pipe: The function to run for this pipe. Should not take any arguments
        :keyword string name:  The command-line name of this pipe (no spaces, `+`, `-`)
        :keyword string description: A short description, which will be used by the logger when displaying information about the pipe
        :keyword tuple exceptions: A tuple of exceptions which are acceptable results for this pipe. These exceptions will be caught and logged, but will allow the pipeline to continue. These exceptions will still raise errors in Debug mode.
        :keyword bool include: A boolean, Whether to include this pipe in the `*all` macro or not.
        :keyword string help: Help text for the command line argument. A value of False excludes the help, None includes generic help.
        :keyword list dependencies: An ordered list of the pipes which must run before this pipe can run. Dependencies will be deep-searched.
        :keyword list replaces: A list of pipes which can be replaced by this pipe. This pipe will now satisfy those dependencies.
        :keyword bool optional: A boolean about wheather this pipe can be skipped. If so, warnings will not be raised when this pipe is explicitly skipped (like ``-pipe`` would do)
        
        
    	Pipes are called with either a ``+`` or ``-`` character at the beginning. Their resepctive actions are shown below.
	
    	========= ============ ================================
    	Character  Action      Description
    	========= ============ ================================
    	``-``     Exclude      To exclude a pipe, use ``-pipe``. This pipe (and it's dependents) will be skipped.
    	``+``     Include-only To include a pipe and the dependents of that pipe, use ``+pipe``.
    	========= ============ ================================
        
        Pipes cannot be added dynamically. Once the pipeline starts running (i.e. processing pipes) the order and settings are fixed. Attempting to adjsut the pipes at this point will raise an error.
        """
        if self.state["started"]:
            raise PipelineStateException("Cannot add a new pipe to the pipeline, the simulation has already started!")
        
        pipe = Pipe(action=action,module=self.__module__,**kwargs)
        if pipe.name in self.pipes:
            raise PipelineException("Cannot have duplicate pipe named %s" % name)
        
        self.pipes[pipe.name] = pipe
        self.pos_pipe_parser.add_argument("+"+pipe.name,action='append_const',dest='include',const=pipe.name,help=pipe.help)
        self.neg_pipe_parser.add_argument("-"+pipe.name,action='append_const',dest='exclude',const=pipe.name,help=argparse.SUPPRESS)
        if pipe.include:
            self.pipes["all"].dependencies += [pipe.name]
        
        
    def register_config(self,configuration,*arguments,**kwargs):
        """Registers a bulk configuration option which will be provided with the USAGE statement. This configuration option can easily override normal configuration settings. Configuration provided here will override programmatically specified configuration options. It will not override configuration provided by the configuration file. These configuration options are meant to provide alterantive *defaults*, not alternative configurations.
        
        :param string argument: The command line argument (e.g. ``-D``)
        :param dict configuration: The configuration dictionary to be merged with the master configuration.
        :keyword bool preconfig: Applies these adjustments before loading the configuration file.
        
        Other keyword arguments are passed to :meth:`ArgumentParser.add_argument`
        """
        if self.state["started"]:
            raise PipelineStateError("Cannot add configuration extra after pipeline has started!")
        
        if "help" not in kwargs:
            help = argparse.SUPPRESS
        else:
            help = kwargs["help"]
            del kwargs["help"]
                
        if kwargs.get("pre_configure",False):
            dest = 'pre_configure'
        else:
            dest = 'post_configure'
            
        self.config_parser.add_argument(*arguments,action='append_const',dest=dest,const=configuration,help=help,**kwargs)
        
    def collect(self, matching=r'^(?!\_)', genericClasses=(), collectionObjects=(),**kwargs):
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
        for cInstance in collectionObjects:
            currentList += dir(cInstance)
        pipeList = []
        for methodname in currentList:
            if (methodname not in genericList):
                method = getattr(self,methodname)
                if callable(method) and ( re.search(matching,methodname) or getattr(method,'collect',False) ) and ( not getattr(method,'ignore',False) ):
                    pipeList.append(method)
        
        pipeList.sort(key=func_lineno)
        [ self.register_pipe(pipe,**kwargs) for pipe in pipeList ]
        
    
    def configure(self):
        """Configure this pipeline object"""
        if not getattr(self._opts,'pre_configure',False):
            self.opts.pre_configure = []
        if not getattr(self._opts,'post_configure',False):
            self.opts.post_configure = []
        if not getattr(self._opts,'include',False):
            self.opts.include = []
        if not getattr(self._opts,'exclude',False):
            self.opts.exclude = []
        
        for cfg in self.opts.pre_configure:
            self.config.update(cfg)
        super(Pipeline, self).configure()
        for cfg in self.opts.post_configure:
            self.config.update(cfg)
        self.set_state("configured")
            
    def parse(self):
        """Parse this object."""
        super(Pipeline, self).parse()
        for pipename in self.opts.include:
            self.pipes[pipename].set_state("included")
        for pipename in self.opts.exclude:
            self.pipes[pipename].set_state("excluded")
        self.set_state("parsed")
        all_pipe = self.pipes.pop("all")
        self.pipes["all"] = all_pipe
        self.resolve()
        
        
    #########################
    ## PIPELINE RESOLUTION ##
    #########################
        
    def resolve(self):
        """Resolve this system's order."""
        self.set_state("started")
        self.call = []
        self.levels = 0
        for pipe in self.pipes.values():
            if self._unprimed(pipe) and pipe.state["included"]:
                self._resolve(pipe)
        for pipe in self.pipes.values():
            if (pipe.state["primed"] or pipe.state["triggered"]) and (not pipe.state["replaced"]):
                self.call += [pipe]
    
    def _resolve(self,pipe):
        """docstring for _resolve"""
        self._resolve_dependents(pipe)
        pipe.set_state("primed")
        self._resolve_triggers(pipe)
        self._resolve_replaces(pipe)
    
    def _unprimed(self,pipe):
        """docstring for _primed"""
        return not pipe.state["primed"] and not pipe.state["excluded"]
    
    def _resolve_dependents(self,parent_pipe):
        """Handle dependents for this pipe"""
        order_error = True
        for pipe in reversed(self.pipes.values()):
            if pipe.name == parent_pipe.name:
                order_error = False
            if pipe.name in parent_pipe.dependencies and self._unprimed(pipe):
                if order_error:
                    raise PipelineStateException("Pipe {a:s} cannot depend on pipe {b:s} because {a:s} must run before {b:s}".format(a=parent_pipe.name,b=pipe.name))
                pipe.parent = parent_pipe.name
                self._resolve(pipe)
        
    def _resolve_triggers(self,parent_pipe):
        """Handle triggers for this pipe"""
        order_error = False
        for pipe in reversed(self.pipes.values()):
            if pipe.name == parent_pipe.name:
                order_error = True
            if pipe.name in parent_pipe.triggers and self._unprimed(pipe) and not pipe.state["included"]:
                if order_error:
                    raise PipelineStateException("Pipe {a:s} cannot trigger pipe {b:s} because {a:s} must run after {b:s}".format(a=parent_pipe.name,b=pipe.name))
                pipe.parent = parent_pipe.name
                pipe.set_state("triggered")
                self._resolve(pipe)
                
    def _resolve_replaces(self,parent_pipe):
        """Handle replacements for this pipe"""
        for pipe in reversed(self.pipes.values()):
            if pipe.name in parent_pipe.replaces:
                pipe.set_state("replaced")
    
    
    def get_dependency_tree(self):
        """Collect the dependency tree"""
        tree = []
        for pipe in reversed(self.call):
            if pipe.state["included"]:
                tree += pipe.tree(self.pipes.values(),0)
        return tree
        
    def get_profile(self):
        """Get the profile object."""
        return Profile(self)
    
    
    ######################
    ## PIPELINE ACTIONS ##
    ######################
    
    def do(self):
        """The action verb!"""
        self.start_actions()
        if not self.call:
            self.parser.error("No stages were set to run!")
        for pipe in self.call:
            self._execute(pipe)
        self.end_actions()
        
    def start_actions(self):
        """Actions completed before running the system."""
        if self.config.get("System.DryRun",False):
            self.log.status("(DRYRUN) Starting...")
        else:
            self.log.status("Starting...")
            
    def end_actions(self):
        """Actions completed after running the system."""
        self.log.status("Finishing...")
        if self.config.get("Actions.ShowTree",False):
            print "\n".join(self.get_dependency_tree())
        if self.config.get("Actions.Profile",False):
            self.get_profile().to_txt()
        
    def execute(self,pipename):
        """Execute an individual pipe by name."""
        self._execute(self.pipes[pipename])
        
    def _execute(self,pipe):
        """Execute an individual pipe object."""
        try:
            pipe.run(dry=self.config.get("System.DryRun",False))
        except (SystemExit,KeyboardInterrupt):
            print(" ...killed... ") #This accounts for the User's ^C in the stdout stream.
            self.log.critical(u"Keyboard Interrupt during %(pipe)s... ending simulator." % { 'pipe': pipe.name })
            self.log.critical(u"Last completed pipe: %(pipe)s" % { 'pipe': self.completed[-1] })
            self.log.debug(u"Pipes completed: %s" % ", ".join(self.completed))
            raise
            