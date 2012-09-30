# -*- coding: utf-8 -*-
# 
#  backup.py
#  pyshell
#  
#  Created by Alexander Rudy on 2012-09-29.
#  Copyright 2012 Alexander Rudy. All rights reserved.
# 
from argparse import ArgumentParser
from pkg_resources import resource_filename
from subprocess import Popen
import yaml
import subprocess
import os, os.path

backup_rsync = 'rsync'
parser_description = u"""
BackUp – A simple backup utility using {rsync}.
""".format(rsync=backup_rsync)

def force_dir_path(path):
    """Force the input path to be a directory."""
    if not path.endswith("/"):
        return path + "/"
    elif path.endswith("//"):
        return path.rstrip("/") + "/"
    else:
        return path

class BackupEngine(object):
    """The controlling engine for backups."""
    def __init__(self):
        super(BackupEngine, self).__init__()
        self._parser = ArgumentParser(description = parser_description, prefix_chars='-+')
        self._parser.add_argument('-n','--dry-run',help="Print what would be copied, but don't copy",action='store_false',dest='run')
        self._parser.add_argument('-q',help="Silence the noisy output",action='store_false',dest='verbose')
        self._parser.add_argument('-d','--delete',help="Delete duplicated files",action='store_true')
        self._parser.add_argument('--print',help="Print commands",action='store_true',dest='prints')
        self._parse_modes = self._parser.add_argument_group('Targets')
        self._destinations = {}
        self._origins = {}
        self._delete = {}
        self._pargs = [backup_rsync,'-a']
        self._procs = {}
        self._home = os.environ["HOME"]
        
    def set_destination(self,argname,origin,destination,delete=False):
        """Set a backup route for rsync"""
        destination = destination.replace("~",self._home)
        destination = force_dir_path(destination)
        origin = origin.replace("~",self._home)
        origin = force_dir_path(origin)
        self._destinations[argname] = destination
        self._origins[argname]      = origin
        self._delete[argname]       = delete
        self._parse_modes.add_argument('+'+argname,
            help="Copy files from {origin} to {destination}".format(origin=origin,destination=destination),action='append_const',dest='modes',const=argname)
        
    def parse_arguments(self):
        """Parse the command line arguments"""
        args = self._parser.parse_args()
        self._modes     = args.modes
        self._run       = args.run
        self._verbosity = args.verbose
        self._print     = args.prints
        if not self._modes:
            self._parser.error("No backup routine selected. Must select at least one:")
        
    def setup_args(self):
        """Setup process arguments"""
        if self._verbosity:
            self._pargs += ['-v']
        if not self._run:
            self._pargs += ['-n']
        
    def start_proc(self,mode):
        """Operate on a given mode"""
        _pargs = self._pargs + [ self._origins[mode] , self._destinations[mode] ]
        if not os.path.isdir(self._origins[mode]):
            print "Skipping {mode} backup. Origin {origin} does not exist.".format(mode=mode,origin=self._origins[mode])
            return
        if not os.path.isdir(self._destinations[mode]):
            print "Skipping {mode} backup. Destination {destination} does not exist.".format(mode=mode,destination=self._destinations[mode])
            return
        if self._delete[mode]:
            _pargs += ['--del']
            print "WARNING: {mode} is using '--del'.".format(mode=mode)
        print "Starting {mode} backup.".format(mode=mode)
        if self._print:
            print " ".join(_pargs)
        if self._run:
            self._procs[mode] = Popen(_pargs)
        
        
    def start(self):
        """Run all the given stored processes"""
        for mode in self._modes:
            self.start_proc(mode)
        
    def end_proc(self,mode):
        """Wait for a particular process to end."""
        if mode in self._procs:
            self._procs[mode].wait()
            print "Finished {mode} backup.".format(mode=mode)
        else:
            print "Mode {mode} was never started.".format(mode=mode)
        
    def end(self):
        """End all processes"""
        for mode in self._modes:
            self.end_proc(mode)
        
    def configure(self):
        """Configure the simulator"""
        if os.access('Backup.yaml',os.F_OK):
            with open('Backup.yaml','r') as filestream:
                config = yaml.load(filestream)
        else:
            with open(resource_filename(__name__,'Defaults.yaml'),'r') as filestream:
                config = yaml.load(filestream)
        
        dest_prefix = config.pop('destination',"")
        orig_prefix = config.pop('origin',"")
        
        for mode,mcfg in config.iteritems():
            destination = dest_prefix + mcfg.get("destination","")
            origin = orig_prefix + mcfg.get("origin","")
            self.set_destination(argname = mode, origin = origin, destination = destination, delete = mcfg.pop('delete',False))
            
            
    def run(self):
        """Run the whole engine"""
        self.configure()
        self.parse_arguments()
        self.setup_args()
        self.start()
        self.end()
            
def script():
    """Operations if this module is a script"""
    engine = BackupEngine()
    engine.run()