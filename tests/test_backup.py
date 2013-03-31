# -*- coding: utf-8 -*-
# 
#  test_backup.py
#  pyshell
#  
#  Created by Alexander Rudy on 2012-09-30.
#  Copyright 2012 Alexander Rudy. All rights reserved.
# 

import shutil, os, os.path
import pyshell.backup
import nose.tools as nt
import warnings
from nose.plugins.skip import Skip,SkipTest
from subprocess import CalledProcessError, Popen, PIPE
import nose.tools as nt


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
    """pyshell.backup.BackupEngine"""
    
    @nt.raises(CalledProcessError)
    def test_command_change(self):
        """Change command to 'scp' fails."""
        engine = pyshell.backup.BackupEngine(cmd='scp')
        
    def test_set_destination(self):
        """Set destinations."""
        engine = pyshell.backup.BackupEngine()
        engine.set_destination('test1','a/','b/','test2')
        engine.set_destination('test2','a/','c/','test3')
        nt.eq_(engine._destinations['test2'].destination, 'c/')
        nt.eq_(engine._destinations['test1'].destination, 'b/')
        
    def test_set_destination_duplicates(self):
        """Set duplicate destinations."""
        engine = pyshell.backup.BackupEngine()
        with warnings.catch_warnings(record=True) as warned:
            warnings.simplefilter("always")
            engine.set_destination('test1','a/','b/','test2')
            engine.set_destination('test1','a/','c/','test3')
        nt.eq_(warned[0].message.message, "Mode test1 will be overwritten.")
        nt.eq_(engine._destinations['test1'].destination, 'c/')
        
    

class test_BackupScript(object):
    """pyshell.backup.BackupEngine.script()"""
    
    NUM_FILES = 50
    SKIP_FACT = 5
    
    def setup(self):
        """Set up the environment"""
        
        self.PATH = os.path.relpath(os.path.dirname(__file__))
        self.EXEPATH = os.path.relpath(os.path.dirname(pyshell.backup.__file__))
        
        clear_dir(os.path.join(self.PATH,'a/'))
        make_files(os.path.join(self.PATH,'a/'),self.NUM_FILES)
        
        clear_dir(os.path.join(self.PATH,'b/'))
        clear_dir(os.path.join(self.PATH,'c/'))
        make_files(os.path.join(self.PATH,'c/'),self.NUM_FILES)

        clear_dir(os.path.join(self.PATH,'d/'))
        for i in range(self.NUM_FILES/self.SKIP_FACT):
            shutil.copy2(os.path.join(self.PATH,'c/c.%03d.test' % (i * self.SKIP_FACT)),os.path.join(self.PATH,'d/'))
            
        self.engine = pyshell.backup.BackupEngine()
        self.engine.init()
    
    def teardown(self):
        """Tear down the environment"""
        clear_dir(os.path.join(self.PATH,'a/'))
        clear_dir(os.path.join(self.PATH,'b/'))
        clear_dir(os.path.join(self.PATH,'c/'))
        clear_dir(os.path.join(self.PATH,'d/'))
        
    
    def test_engine_full(self):
        """Test full engine"""
        assert len(os.listdir(os.path.join(self.PATH,'a/'))) != len(os.listdir(os.path.join(self.PATH,'b/')))
        assert len(os.listdir(os.path.join(self.PATH,'c/'))) != len(os.listdir(os.path.join(self.PATH,'d/')))
        self.engine.arguments("-q --config tests/Backup.yaml main other".split())
        self.engine.run()
        print os.listdir(os.path.join(self.PATH,'a/'))
        print os.listdir(os.path.join(self.PATH,'b/'))
        nt.eq_(len(os.listdir(os.path.join(self.PATH,'a/'))), len(os.listdir(os.path.join(self.PATH,'b/'))))
        nt.eq_(len(os.listdir(os.path.join(self.PATH,'c/'))), len(os.listdir(os.path.join(self.PATH,'d/'))))
        
    def test_engine_subproc(self):
        """Test full engine as a subprocess."""
        assert len(os.listdir(os.path.join(self.PATH,'a/'))) != len(os.listdir(os.path.join(self.PATH,'b/')))
        assert len(os.listdir(os.path.join(self.PATH,'c/'))) != len(os.listdir(os.path.join(self.PATH,'d/')))
        backup_py_path = os.path.join(self.EXEPATH,"backup.py")
        backup_py_config = os.path.join(self.PATH,"Backup.yaml")
        backup_py_args = ("python %s -q --config %s main other" % (backup_py_path,backup_py_config)).split()
        backup_py = Popen(backup_py_args,stdin=PIPE,stdout=PIPE,stderr=PIPE)
        backup_py_retcode = backup_py.wait()
        nt.eq_(backup_py_retcode, 0)
        nt.eq_(len(os.listdir(os.path.join(self.PATH,'a/'))), len(os.listdir(os.path.join(self.PATH,'b/'))))
        nt.eq_(len(os.listdir(os.path.join(self.PATH,'c/'))), len(os.listdir(os.path.join(self.PATH,'d/'))))
        
        