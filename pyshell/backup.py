# -*- coding: utf-8 -*-
# 
#  backup.py
#  pyshell
#  
#  Created by Alexander Rudy on 2012-09-29.
#  Copyright 2012 Alexander Rudy. All rights reserved.
# 
from argparse import ArgumentParser, SUPPRESS, RawDescriptionHelpFormatter
from pkg_resources import resource_filename
from subprocess import Popen
import yaml
import subprocess
import os, os.path
from textwrap import fill
from warnings import warn

from . import version
from .util import force_dir_path
from .base import CLIEngine

class BackupEngine(CLIEngine):
    """The controlling engine for backups."""
    
    @property
    def description(self):
         return fill(u"BackUp – A simple backup utility using {cmd}. The utility has configurable targets, and can spawn multiple simultaneous {cmd} processes for efficiency.".format(cmd=self._cmd))+"\n\n"+fill("Using {version}".format(version=self._cmd_version))
        
    defaultcfg = "Backup.yml"
    
    def __init__(self,cmd="rsync"):
        self._cmd = cmd
        self._cmd_version = subprocess.check_output([self._cmd,'--version'],stderr=subprocess.STDOUT).split("\n")[0]
        super(BackupEngine, self).__init__()
        self._parser.add_argument('--prefix',action='store',metavar='path/to/',nargs='+',default=[],help="Set the backup prefixes")
        self._destinations = {}
        self._origins = {}
        self._delete = {}
        self._triggers = {}
        self._pargs = [self._cmd,'-a']
        self._procs = {}
        self._help = []
            
    def set_destination(self,argname,origin,destination,delete=False,triggers=None):
        """Set a backup route for rsync"""
        # Normalize Arguments
        destination = force_dir_path(os.path.expanduser(destination))
        origin      = force_dir_path(os.path.expanduser(origin))
        triggers    = triggers if isinstance(triggers,list) else []
        
        # Set Properties
        self._destinations[argname] = destination
        self._origins[argname]      = origin
        self._delete[argname]       = delete
        self._triggers[argname]     = triggers
        
        # Set program help:
        self._help += [ "  %(mode)-18s Copy files using the '%(mode)s' target %(delete)s\n%(s)-20s  from %(origin)r\n%(s)-20s  to   %(destination)r\n" % dict(s=" ",mode=argname,origin=origin,destination=destination,delete="removing old files" if delete else "") ]
        
    def parse(self):
        """Parse the command line arguments"""
        self._parser.add_argument('-n','--dry-run',action='store_false',dest='run',help="Print what would be copied, but don't copy")
        self._parser.add_argument('-q',action='store_false',dest='verbose',help="Silence the noisy output")
        self._parser.add_argument('-d','--delete',action='store_true',dest='delete',help="Delete duplicated files")
        self._parser.add_argument('-v','--print',action='store_true',dest='prints',help="Print {cmd} commands".format(cmd=self._cmd))
        self._parser.add_argument('--version',action='version',version="%(prog)s version {version}\n{cmd_version}".format(version=version,cmd_version=self._cmd_version))
        self._parser.add_argument('modes',metavar='target',nargs='+',default=[],help="The %(prog)s target's name.")
        self._parser.epilog = "\n".join(self._help)
        super(BackupEngine, self).parse()
        
        if not self._opts.modes:
            self._parser.error("No backup routine selected. Must select at least one:\n+%s" % " +".join(self._origins.keys()))
        self.setup_args()
        
        
    def setup_args(self):
        """Setup process arguments"""
        if self._opts.verbose:
            self._pargs += ['-v']
        if not self._opts.run:
            self._pargs += ['-n']
        
    def start_proc(self,mode):
        """Operate on a given mode"""
        if not (mode in self._origins or mode in self._destinations or mode in self._delete):
            warn("Mode {mode} not found!".format(mode=mode),UserWarning)
            return
        elif not (mode in self._origins and mode in self._destinations and mode in self._delete):
            warn("Mode {mode} incomplete!".format(mode=mode),UserWarning)
        _pargs = self._pargs + [ self._origins[mode] , self._destinations[mode] ]
        if mode in self._procs:
            warn("Mode {mode} already running.".format(mode=mode),RuntimeWarning)
            return
        elif not os.path.isdir(self._origins[mode]):
            warn("Skipping {mode} backup. Origin {origin} does not exist.".format(mode=mode,origin=self._origins[mode]),RuntimeWarning)
            return
        elif not os.path.isdir(self._destinations[mode]):
            warn("Skipping {mode} backup. Destination {destination} does not exist.".format(mode=mode,destination=self._destinations[mode]),RuntimeWarning)
            return
        if self._delete[mode] or self._opts.delete:
            _pargs += ['--del']
            warn("{mode} is using '--del'.".format(mode=mode),UserWarning)
        print("Starting {mode} backup...".format(mode=mode))
        if self._opts.prints:
            print(" ".join(_pargs))
        self._procs[mode] = Popen(_pargs)
        for tmode in self._triggers[mode]:
            self.start_proc(mode)
        
        
    def start(self):
        """Run all the given stored processes"""
        for mode in self._opts.modes:
            self.start_proc(mode)
        
    def end_proc(self,mode):
        """Wait for a particular process to end."""
        if mode in self._procs:
            retcode = self._procs[mode].wait()
            if retcode != 0:
                warn("Mode {mode} exited abmnormally with code {code}".format(mode=mode,code=retcode),RuntimeWarning)
            print("Finished {mode} backup.".format(mode=mode))
        elif mode not in self._origins:
            return
        else:
            warn("Mode {mode} was never started.".format(mode=mode),UserWarning)
        
    def end(self):
        """End all processes"""
        for mode in self._opts.modes:
            self.end_proc(mode)
        
    def kill_proc(self,mode):
        """Kill a particular subprocess"""
        if mode in self._procs:
            retcode = self._procs[mode].terminate()
            if retcode != 0:
                warn("Mode {mode} terminated with code {code}".format(mode=mode,code=retcode),RuntimeWarning)
            print("Terminated {mode} backup".format(mode=mode))
        elif mode not in self._origins:
            return
        else:
            warn("Mode {mode} was never started.".format(mode=mode),UserWarning)
            
    def kill(self):
        """Kill all mode procedures"""
        for mode in self._opts.modes:
            self.kill_proc(mode)
    
    def configure(self):
        """Configure the simulator"""
        super(BackupEngine, self).configure()
        
        if len(self._opts.prefix) == 2:
            self._config["destination"] = self._opts.prefix[1]
            self._config["origin"] = self._opts.prefix[0]
        elif len(self._opts.prefix) == 1:
            self._config["destination"] = self._opts.prefix[0]
        elif len(self._opts.prefix) > 2:
            self._parser.error("Cannot specificy more than two prefixes. Usage: --prefix [origin] destination")
        
        self._help += ['Configured from \'%s\'' % self._opts.config,'','targets:']
        
        dest_prefix = self._config.pop('destination',"")
        orig_prefix = self._config.pop('origin',"")
        
        for mode,mcfg in self._config.iteritems():
            destination = dest_prefix + mcfg.get("destination","")
            origin = orig_prefix + mcfg.get("origin","")
            self.set_destination(argname = mode, origin = origin, destination = destination, delete = mcfg.pop('delete',False))
            
            
        
    
if __name__ == '__main__':
    print("Running from file: {arg}".format(arg=sys.argv[0]))
    engine = BackupEngine()
    engine.arguments()
    engine.run()

