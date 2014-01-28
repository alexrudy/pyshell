# 
#  test_bump_version.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-04-02.
#  Copyright 2013 Alexander Rudy. All rights reserved.
# 

import nose.tools as nt
import pyshell.bump_version
import shlex
import pkg_resources
import os, shutil

class test_bump_version(object):
    """Bump Version"""
    CLASS = pyshell.bump_version.VersionBumper
    
    def setup(self):
        """docstring for setup"""
        self.filepath = pkg_resources.resource_filename(__name__,'test_bump_version/')
        shutil.copy(os.path.join(self.filepath,'vtest.py.original'),os.path.join(self.filepath,'vtest.py'))
    
    def teardown(self):
        """Remove vtest.py"""
        if os.path.exists(os.path.join(self.filepath,'vtest.py')):
            os.remove(os.path.join(self.filepath,'vtest.py'))
        if os.path.exists(os.path.join(self.filepath,'vtest.py.backup')):
            os.remove(os.path.join(self.filepath,'vtest.py.backup'))
    
    @nt.nottest
    def file_eq(self, file_a, file_b):
        """docstring for read"""
        with open(file_a, 'r') as stream:
            file_a_lines = stream.read().splitlines()
        with open(file_b, 'r') as stream:
            file_b_lines = stream.read().splitlines()
            
        nt.eq_("\n".join(file_a_lines), "\n".join(file_b_lines))
    
    def test_script(self):
        """Test the script"""
        ENG = self.CLASS()
        ENG.arguments(shlex.split("0.2.3 --glob *.py -C %s" % self.filepath))
        ENG.run()
        self.file_eq(os.path.join(self.filepath,'vtest.py'),os.path.join(self.filepath,'vtest.py.answer'))
        