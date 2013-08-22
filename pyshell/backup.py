#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
#  backup.py
#  pyshell
#  
#  Created by Alexander Rudy on 2012-09-29.
#  Copyright 2012 Alexander Rudy. All rights reserved.
#
"""
BackUp - A command-line backup tool.
"""

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)


from subprocess import Popen
import subprocess
import os, os.path
import sys
import argparse
from textwrap import fill
from warnings import warn

try:
    from . import version, CLIEngine, PYSHELL_LOGGING_STREAM
    from .util import force_dir_path, is_remote_path
except ValueError:
    from pyshell import version, CLIEngine, PYSHELL_LOGGING_STREAM
    from pyshell.util import force_dir_path, is_remote_path

__all__ = ['BackupEngine']

class _BackupDestination(object):
    """Private class for managing backup destinations"""
    def __init__(self, name, command='rsync', destination=None, origin=None, 
        delete=False, triggers=None, reverse=False, reversedel=False):
        super(_BackupDestination, self).__init__()
        self.name = name
        self.pseudo = destination is None or origin is None
        self.command = command
        self._destination = destination
        self._origin = origin
        self.delete = delete
        self.reverse = reverse
        self.reversedel = reversedel
        if triggers is None:
            triggers = []
        self.triggers = triggers
        self._process = False
        self._returncode = None
        self._pargs = [ self.command ]
        if self.pseudo and not (destination is None and origin is None):
            raise AttributeError("Missing destination or orign")
        
    @property
    def operable(self):
        """Whether this mode would run or not."""
        return (not self.pseudo) or (self.triggers)
        
    @property
    def running(self):
        """Accessor for the process argument."""
        return isinstance(self._process,Popen) and getattr(self._process,'returncode',None) is None
        
    @property
    def returncode(self):
        """The return code for the running process"""
        return self._returncode
        
    @property
    def destination(self):
        """The endpoint for this rsync destination"""
        return os.path.expanduser(self._destination)
        
    @property
    def origin(self):
        """The origin point for this rsync destination"""
        return os.path.expanduser(self._origin)
        
    @property
    def remote(self):
        """Detect if either path is remote"""
        return is_remote_path(self.origin) , is_remote_path(self.destination)
        
    @property
    def paths(self):
        """Return the correct path pair arguments"""
        if self.reverse:
            return [self.destination, self.origin]
        else:
            return [self.origin, self.destination]
        
    def launch(self,args,delete=False,prints=False,reverse=None):
        """Launch this process with the sequence of arguments."""
        if self.pseudo:
            return True
        
        if not isinstance(self.origin,basestring) or not isinstance(self.destination,basestring) \
            or not isinstance(self.delete,bool):
            raise ValueError("Mode {mode} is incomplete.".format(mode=self.name))
        
        if reverse is not None:
            self.reverse = reverse
        
        # Check that the mode isn't running, and that the mode's
        # destination and origin directories exist.
        if self.running:
            warn("Mode '{mode}' already running.".format(mode=self.name),
                RuntimeWarning)
            return False
        elif not (os.path.isdir(self.origin) or self.remote[0]):
            warn("Skipping '{mode}' backup. Origin '{origin}' does not "\
                "exist.".format(mode=self.name,origin=self.origin),
                RuntimeWarning)
            return False
        elif not (os.path.isdir(self.destination) or self.remote[1]):
            warn("Skipping '{mode}' backup. Destination '{destination}' "\
                "does not exist.".format(mode=self.name,
                    destination=self.destination),
                RuntimeWarning)
            return False
        
        # Set up this command's arguments
        self._pargs += list(args) + self.paths
        
        # Check whether we should use the '--del' option
        if (self.delete or delete) and ((self.reverse and\
            self.reversedel) or (not self.reverse)):
            self._pargs += ['--del']
            warn("{mode} is using '--del'.".format(mode=self.name), UserWarning)
        elif (self.delete or delete) and not ((self.reverse and\
            self.reversedel) or (not self.reverse)):
            warn("{mode} is not using '--del' because '--reverse' is set. To \
            override this, please use '--reverse-delete'".format(mode=self.name), UserWarning)
        
        print("Starting {mode} backup... {dryrun}".format(mode=self.name,dryrun="" if "-n" not in self._pargs else "(DRY RUN)"))
        
        # Print the command
        if prints:
            print(" ".join(self._pargs))
        
        # Run the command
        self._process = Popen(self._pargs)
        self._returncode = None
        
        return True
        
    def wait(self):
        """Wait for this command to complete"""
        self._returncode = self._process.wait()
        if self.returncode != 0:
            warn("Mode {mode} exited abmnormally with code "\
                "{code}".format(mode=self.name,code=self.returncode), RuntimeWarning)
        print("Finished {mode} backup.".format(mode=self.name))
        
        
    def kill(self):
        """Kill this command's process"""
        if self.running:
            self._process.terminate()
            self._returncode = self._process.wait()
            if self.returncode != 0:
                warn("Mode {mode} terminated with code "\
                    "{code}".format(mode=self.name, code=self.returncode), RuntimeWarning)
            print("Terminated {mode} backup".format(mode=self.name))
            return self._returncode == 0
        else:
            warn("Mode {mode} was never started.".format(mode=self.name),
                UserWarning)
            return False
        
        
    def help(self):
        """Return the constructed help string for this object."""
        if self.pseudo:
            helpstring = "  %(mode)-18s Trigger modes %(triggers)s" \
                % dict(mode=self.name,triggers=",".join(self.triggers))
        else:
            helpstring = "  %(mode)-18s Copy files using the '%(mode)s' target "\
                "%(delete)s\n%(s)-20s  from '%(origin)s'\n%(s)-20s  to   "\
                "'%(destination)s'\n" % dict(s=" ", mode=self.name, origin=self.origin,
                    destination=self.destination,
                    delete="removing old files" if self.delete else "")
        return helpstring
        
        

class BackupEngine(CLIEngine):
    """The controlling engine for backups."""
    
    @property
    def description(self):
        """
        A text description of the BackUp Engine.
        
        Implemented as a property to allow the text description to include
        infomration about the underlying command, usually `rsync`.
        """
        return fill("BackUp – A simple backup utility using {cmd}. The "\
        "utility has configurable targets, and can spawn multiple "\
        "simultaneous {cmd} processes for efficiency.".format(cmd=self._cmd))\
        + "\n\n" + fill("Using {version}".format(version=self._cmd_version))
        
        
    @property
    def epilog(self):
        """A text epilog"""
        return fill("Any arguments not parsed by this tool will be passed to {cmd}".format(cmd=self._cmd))
        
    cfgbase = ""
    
    defaultcfg = "Backup.yml"
    
    debug = False
    
    supercfg = PYSHELL_LOGGING_STREAM
    
    def __init__(self, cmd="rsync"):
        # - Initialization of Command Variables
        # This code all comes before the call to `super` so that the 
        # `self._cmd` variable is set properly and the `self._cmd_version`
        # variable is also set when the `super` call asks for the description,
        # the description property can correctly incorporate information about
        # the name and version of the command in use.
        self._cmd = cmd
        self._cmd_version = subprocess.check_output(
            [self._cmd,'--version'],
            stderr=subprocess.STDOUT,
            ).split("\n")[0] # We take only the first line
        # - End initialization of Command Variables
        super(BackupEngine, self).__init__()
        
        self._destinations = {}
        self._help  = [    ]
        self._pargs = ['-a','--partial']
    
    def init(self):
        """Initialize the command line arguments"""
        super(BackupEngine, self).init()
        # This argument should be parsed before the help
        # text is created to dynamically include this info
        # in the help screen.
        self.parser.add_argument('--prefix',
            action='store', default=[],
            metavar='path/to/', nargs='+',
            help="Set the backup prefixes")
        self.parser.add_argument('--root',
            action='store_false',dest='cwd',
            help="Use the root ('/') directory as origin base")
        self.parser.add_argument('-r','--reverse',
            action='store_true',
            help="Flip destination and origin flags." \
            "Will disable any --del flag.")
        self.parser.add_argument('--reverse-delete',
            action='store_true',dest='reversedel',
            help="Use --del flag even when reversed.")
        self.parser.usage = "%(prog)s [-nqdvpr] [--config file.yml] [--prefix "\
        "origin [destination] | --root ]\n            target [target ...] {{{cmd} args}}".format(cmd=self._cmd)
        
    @property
    def backup_config(self):
        """docstring for backup_config"""
        if self.cfgbase == "":
            return self.config
        else:
            return self.config[self.cfgbase]
    
    def set_destination(self, argname, origin=None, destination=None,
        delete=False, triggers=None):
        """Set a backup route for rsync"""
        
        if argname in self._destinations:
            warn("Mode {mode} will be overwritten.".format(mode=argname),
            UserWarning)
        
        # Normalize Arguments
        if destination is not None or origin is not None:
            destination = os.path.expanduser(destination)
            origin      = os.path.expanduser(origin)
        triggers    = triggers if isinstance(triggers, list) else []
        reverse     = getattr(self.opts,'reverse',False)
        
        # Set Properties
        self._destinations[argname] = _BackupDestination(
            name = argname,
            command = self._cmd,
            destination = destination,
            origin = origin,
            delete = delete,
            triggers = triggers,
            reverse = reverse,
            reversedel = getattr(self.opts,'reversedel',False)
        )
        
        if self._destinations[argname].operable:
            # Set program help:
            self._help += [self._destinations[argname].help()]
        else:
            del self._destinations[argname]
        
    def parse(self):
        """Parse the command line arguments"""
        super(BackupEngine, self).parse()
        
        if not self.opts.modes:
            self.parser.error("No backup routine selected. "\
            "Must select at least one:\n+%s" % " +".join(self._origins.keys()))
        for mode in self.opts.modes:
            if mode not in self._destinations:
                self.parser.error("Target '{}' does not exist.".format(mode))
        if self.opts.verbose:
            self._pargs += ['-v']
        if not self.opts.run:
            self._pargs += ['-n']
        
        if self.opts.args:
            self._pargs += self.opts.args
    
    def do(self):
        """Run all the given stored processes"""
        for mode in self.opts.modes:
            self._start_mode(mode)
        for mode in self._destinations.keys():
            self._end_mode(mode)
            
    def _start_mode(self,mode):
        """Start a single mode"""
        if self._destinations[mode].launch(self._pargs,prints=self.opts.prints):
            # Run any post-dependent commands.
            map(self._start_mode,self._destinations[mode].triggers)            
        
    def _end_mode(self, mode):
        """Wait for a particular process to end."""
        if self._destinations[mode].running:
            self._destinations[mode].wait()
        
    def _kill_mode(self, mode):
        """Kill a particular subprocess"""
        if self._destinations[mode].running:
            self._destinations[mode].kill()
            
    def kill(self):
        """Kill all mode procedures"""
        for mode in self._destinations.keys():
            self._kill_mode(mode)
    
    def configure(self):
        """Configure the simulator"""
        super(BackupEngine, self).configure()
        
        if len(self.opts.prefix) == 2:
            self.backup_config["destination"] = self.opts.prefix[1]
            self.backup_config["origin"] = self.opts.prefix[0]
        elif len(self.opts.prefix) == 1:
            self.backup_config["destination"] = self.opts.prefix[0]
        elif len(self.opts.prefix) > 2:
            self.parser.error("Cannot specificy more than two prefixes."\
                " Usage: --prefix [origin] destination")
        
        self._help += [ '','', 'Configured from \'%s\'' % self.opts.config,
            '', 'targets:' ]
        
        dest_prefix = self.backup_config.pop('destination',"")
        orig_prefix = self.backup_config.pop('origin',"")
        
        for mode, mcfg in self.backup_config.items():
            if "destination" in mcfg or "origin" in mcfg:
                destination = os.path.join(dest_prefix, mcfg.get("destination",""))
                origin = os.path.join(orig_prefix, mcfg.get("origin",""))
            else:
                destination = None
                origin = None
            self.set_destination(argname = mode, origin = origin,
                destination = destination, delete = mcfg.pop('delete',False), triggers=mcfg.pop("triggers",None))
        
        self.parser.add_argument('-n', '--dry-run', action='store_false',
            dest='run', help="Print what would be copied, but don't copy")
        self.parser.add_argument('-q', action='store_false', dest='verbose',
            help="Silence the noisy output")
        self.parser.add_argument('-d', '--delete', action='store_true',
            dest='delete', help="Delete duplicated files")
        self.parser.add_argument('-v', '--print', action='store_true',
            dest='prints', help="Print {cmd} commands".format(cmd=self._cmd))
        self.parser.add_argument('--version', action='version',
            version="%(prog)s version {version}\n{cmd_version}".format(
                version=version, cmd_version=self._cmd_version))
        self.parser.add_argument('modes', metavar='target', nargs="+", 
            choices=self._destinations.keys() ,default=[], help="The %(prog)s target's name.")
        self.parser.add_argument('args', nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
        self.parser.epilog += "\n".join(self._help)
        
    
if __name__ == '__main__':
    print("Running from file: {arg}".format(arg=sys.argv[0]))
    BackupEngine.script()
    
