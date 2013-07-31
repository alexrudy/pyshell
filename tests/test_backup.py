# -*- coding: utf-8 -*-
# 
#  test_backup.py
#  pyshell
#  
#  Created by Alexander Rudy on 2012-09-30.
#  Copyright 2012 Alexander Rudy. All rights reserved.
# 

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)

import shutil, os, os.path
import pyshell.backup
import nose.tools as nt
import warnings
from nose.plugins.skip import Skip,SkipTest
from subprocess import CalledProcessError, Popen, PIPE
import shlex
from .util import dests_from_argparse


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
        
    def test_attrs(self):
        """BackupEngine attributes"""
        from argparse import ArgumentParser
        engine = pyshell.backup.BackupEngine()
        nt.eq_(engine.description.splitlines()[0],"BackUp – A simple backup utility using rsync. The utility has")
        nt.eq_(engine.cfgbase,'')
        nt.eq_(engine.defaultcfg,"Backup.yml")
        nt.ok_(isinstance(engine.parser,ArgumentParser),"engine.parser should be an argparse.ArgumentParser")

    def test_init_args(self):
        """BackupEngine args set by init()"""
        engine = pyshell.backup.BackupEngine()
        engine.init()
        dests = dests_from_argparse(engine.parser)
        nt.ok_('prefix' in dests,"--prefix missing")
        nt.ok_('cwd' in dests,"--root missing")
        nt.ok_('reverse' in dests,'--reverse missing')
        nt.ok_('reversedel' in dests,'--reverse-delete missing')
        
    def test_backup_config(self):
        """BackupEngine.backup_config"""
        engine = pyshell.backup.BackupEngine()
        if engine.cfgbase == "":
            nt.eq_(engine.backup_config,engine.config,"Backup Config should match full config.")
        else:
            nt.eq_(engine.backup_config,engine.config[cfgbase],"Backup Config should match config['%s']." % engine.cfgbase)
        
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
        
    def test_arguments(self):
        """BackupEngine.arguments()"""
        engine = pyshell.backup.BackupEngine()
        engine.init()
        engine.arguments(["main"])
        nt.eq_(engine._rargs,['main'])
        nt.ok_(hasattr(engine.opts,'prefix'),'engine.opts.mode')
        
    def test_configure(self):
        """BackupEngine.configure()"""
    pass
    

class test_BackupScript(object):
    """pyshell.backup.BackupEngine.script()"""
    
    NUM_FILES = 50
    SKIP_FACT = 5
    
    def setup(self):
        """Set up the environment"""
        
        self.PATH = os.path.relpath(os.path.join(os.path.dirname(__file__),'test_backup'))
        self.EXEPATH = os.path.relpath(os.path.dirname(pyshell.backup.__file__))
        
        try:
            os.makedirs(self.PATH)
        except:
            pass
        
        clear_dir(os.path.join(self.PATH,'a/'))
        make_files(os.path.join(self.PATH,'a/'),self.NUM_FILES)
        
        clear_dir(os.path.join(self.PATH,'b/'))
        clear_dir(os.path.join(self.PATH,'c/'))
        make_files(os.path.join(self.PATH,'c/'),self.NUM_FILES)

        clear_dir(os.path.join(self.PATH,'d/'))
        for i in range(self.NUM_FILES//self.SKIP_FACT):
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
        backup_py_config = os.path.join(self.PATH,"Backup.yaml")
        backup_py_args = shlex.split("-q --config %s main other" % (backup_py_config))
        self.engine.arguments(backup_py_args)
        self.engine.run()
        nt.eq_(len(os.listdir(os.path.join(self.PATH,'a/'))), len(os.listdir(os.path.join(self.PATH,'b/'))))
        nt.eq_(len(os.listdir(os.path.join(self.PATH,'c/'))), len(os.listdir(os.path.join(self.PATH,'d/'))))
        
    def test_engine_subproc(self):
        """Test full engine as a subprocess."""
        assert len(os.listdir(os.path.join(self.PATH,'a/'))) != len(os.listdir(os.path.join(self.PATH,'b/')))
        assert len(os.listdir(os.path.join(self.PATH,'c/'))) != len(os.listdir(os.path.join(self.PATH,'d/')))
        backup_py_path = os.path.join(self.EXEPATH,"backup.py")
        backup_py_config = os.path.join(self.PATH,"Backup.yaml")
        backup_py_command = shlex.split("python %s " % backup_py_path)
        backup_py_args = shlex.split("-q --config %s main other" % backup_py_config)
        backup_py = Popen(backup_py_command + backup_py_args,stdin=PIPE,stdout=PIPE,stderr=PIPE)
        backup_py_retcode = backup_py.wait()
        nt.eq_(backup_py_retcode, 0)
        nt.eq_(len(os.listdir(os.path.join(self.PATH,'a/'))), len(os.listdir(os.path.join(self.PATH,'b/'))))
        nt.eq_(len(os.listdir(os.path.join(self.PATH,'c/'))), len(os.listdir(os.path.join(self.PATH,'d/'))))
        
        