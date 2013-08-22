# -*- coding: utf-8 -*-
# 
#  bump_version.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-01-12.
#  Copyright 2013 Alexander Rudy. All rights reserved.
# 
"""
bump_version -- Increase version numbers!
"""
from __future__ import division
from .base import CLIEngine
import glob, os, os.path, shutil, tempfile
import re

class VersionBumper(CLIEngine):
    """Bump the version of your source code!"""
    
    defaultcfg = "bump_version.yml"
    
    def init(self):
        """docstring for init"""
        super(VersionBumper, self).init()
        self.parser.add_argument('-C','--cwd',type=unicode,dest='cwd',help="Set path",default=os.getcwd())
        self.parser.add_argument('--no-tmp',action="store_false", dest='tmp', help="Use temporary files or backups?")
    
    def after_configure(self):
        """Setup init"""
        super(VersionBumper, self).after_configure()
        self.parser.add_argument('version',type=unicode,help="New version string to use.")
        self.parser.add_argument('--glob',type=unicode,help="File pattern glob for changing versions.",
            default=self.config["glob.files"])
        self.parser.add_argument('--match',type=unicode,help="Match Regex",default=self.config["regex.find"],
            metavar="regexp")
        self.parser.add_argument('--replace',type=unicode,help="Replace Regex",default=self.config["regex.replace"],
            metavar="\"{version}\"")
            
        
    def do(self):
        """Do the actual parsing."""
        version_find = re.compile(self.opts.match.rstrip("\n"))
        version_replace = self.opts.replace.rstrip("\n").format(version=self.opts.version)
        filenames = glob.glob(os.path.join(self.opts.cwd,self.opts.glob))
        if self.opts.tmp:
            filepairs = [(filename, tempfile.mkstemp()[1]) for filename in filenames]
        else:
            filepairs = [(filename, filename+".backup") for filename in filenames]
        try:
            for filename, newname in filepairs:
                with open(filename,'r') as filestream:
                    with open(newname,'w') as outstream:
                        write = outstream.write
                        sub = re.sub
                        for num, line in enumerate(filestream):
                            result = sub(version_find,version_replace,line)
                            write(result)
        except Exception as e:
            raise
        else:
            for filename, newname in filepairs:
                shutil.copy(newname, filename)
        finally:
            for filename,newname in filepairs:
                if os.path.exists(newname):
                    os.remove(newname)
        