# 
#  test_backup.py
#  pyshell
#  
#  Created by Alexander Rudy on 2012-09-30.
#  Copyright 2012 Alexander Rudy. All rights reserved.
# 

import shutil, os, os.path
import pyshell.backup

def clear_dir(tdir):
    """Clear directory"""
    if os.path.isdir(tdir):
        shutil.rmtree(tdir)
    os.mkdir(tdir)
    
def make_files(tdir,N):
    """docstring for make_files"""
    fname = os.path.basename(tdir.rstrip("/"))
    for i in range(N):
        open("%s%s.%03d.test" % (tdir,fname,i),'w').close()
    
    

class test_BackupEngine(object):
    """pyshell.bakcup.BackupEngine"""
    
    NUM_FILES = 50
    SKIP_FACT = 5
    PATH = "tests/"
    
    def setup(self):
        """Set up the environment"""

        clear_dir(self.PATH+'a/')
        make_files(self.PATH+'a/',self.NUM_FILES)
        
        clear_dir(self.PATH+'b/')
        clear_dir(self.PATH+'c/')
        make_files(self.PATH+'c/',self.NUM_FILES)

        clear_dir(self.PATH+'d/')
        for i in range(self.NUM_FILES/self.SKIP_FACT):
            shutil.copy2(self.PATH+'c/c.%03d.test' % (i * 5),self.PATH+'d/')
            
        self.engine = pyshell.backup.BackupEngine()
    
    def teardown(self):
        """Tear down the environment"""
        clear_dir(self.PATH+'a/')
        clear_dir(self.PATH+'b/')
        clear_dir(self.PATH+'c/')
        clear_dir(self.PATH+'d/')
        
    
    def test_engine_full(self):
        """Test full engine"""
        assert len(os.listdir(self.PATH+'a/')) != len(os.listdir(self.PATH+'b/'))
        assert len(os.listdir(self.PATH+'c/')) != len(os.listdir(self.PATH+'d/'))
        self.engine.arguments("-q --config tests/Backup.yaml main other".split())
        self.engine.run()
        assert len(os.listdir(self.PATH+'a/')) == len(os.listdir(self.PATH+'b/'))
        assert len(os.listdir(self.PATH+'c/')) == len(os.listdir(self.PATH+'d/'))