# -*- coding: utf-8 -*-
# 
#  test_base.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-01-12.
#  Copyright 2013 Alexander Rudy. All rights reserved.
# 

import shutil, os, os.path
import pyshell.base
import nose.tools as nt
import warnings
from nose.plugins.skip import Skip,SkipTest
from subprocess import CalledProcessError, Popen, PIPE
import shlex
from .util import dests_from_argparse

class test_base_cliengine(object):
    """pyshell.base.CLIEngine"""
    
    CLASS = pyshell.base.CLIEngine
    
    CONFIG = os.path.join("test_base","config.yml")
    
    CWD = os.path.dirname(__file__)
    
    def setup(self):
        """Setup configuration"""
        import yaml
        cfg = {'a':'b','c':{'d':1}}
        filename = os.path.join(self.CWD,self.CONFIG)
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError:
            pass
        with open(filename,'w') as f:
            yaml.dump(cfg,f,default_flow_style=False,encoding='utf-8')
        
    
    def teardown(self):
        """docstring for teardown_config"""
        try:
            os.remove(os.path.join(self.CWD,self.CONFIG))
        except IOError:
            pass
    
    def test_base_init(self):
        """__init__()"""
        import argparse
        IN = self.CLASS()
        nt.eq_(IN.exitcode,0)
        nt.ok_(isinstance(IN.parser,argparse.ArgumentParser))
        nt.eq_(IN.config.store,{})
        nt.eq_(IN.description,"A command line interface.")
        nt.eq_(IN.epilog,"")
        nt.eq_(IN.defaultcfg,"Config.yml")
        nt.eq_(IN.supercfg,[])
        nt.eq_(IN.opts,None)
    
    def test_argparse(self):
        """.parser arguments"""
        IN = self.CLASS()
        nt.eq_(dests_from_argparse(IN.parser),[])
        IN.init()
        nt.eq_(dests_from_argparse(IN.parser),['config'])
        IN._add_help()
        nt.eq_(dests_from_argparse(IN.parser),['config','help'])
        IN._remove_help()
        nt.eq_(dests_from_argparse(IN.parser),['config'])
        
    def test_init(self):
        """.init()"""
        IN = self.CLASS()
        nt.eq_(dests_from_argparse(IN.parser),[])
        IN.init()
        nt.eq_(dests_from_argparse(IN.parser),['config'])
        self.CLASS.defaultcfg = False
        IN = self.CLASS()
        nt.eq_(dests_from_argparse(IN.parser),[])
        IN.init()
        nt.eq_(dests_from_argparse(IN.parser),[])
        
        
    def test_arguments(self):
        """.arguments()"""
        IN = self.CLASS()
        IN.init()
        IN.arguments(shlex.split("--config file.yml --other value"))
        nt.eq_(IN._rargs,["--other","value"])
        nt.eq_(IN.opts.config,"file.yml")
        nt.eq_(vars(IN.opts),{'config':'file.yml'})
        
    def test_configure(self):
        """.configure()"""
        IN = self.CLASS()
        IN.init()
        IN.arguments(('',))
        IN.opts.config = os.path.join(self.CWD,self.CONFIG)
        IN.configure()
        nt.eq_(IN.config["c.d"],1)
        
    def test_help(self):
        """._add_help() and ._remove_help()"""
        IN = self.CLASS()
        IN.init()
        nt.ok_("help" not in dests_from_argparse(IN.parser))
        IN._add_help()
        nt.ok_("help" in dests_from_argparse(IN.parser))
        IN._remove_help()
        nt.ok_("help" not in dests_from_argparse(IN.parser))
        
    def test_parse(self):
        """.parse()"""
        IN = self.CLASS()
        IN.init()
        IN.arguments(('--hi',))
        nt.eq_(IN._rargs,['--hi'])
        IN.configure()
        IN.parser.add_argument('--hi',action='store_true')
        IN.parse()
        nt.ok_(IN.opts.hi)
        
    def test_parse_fail(self):
        """.parse() failure"""
        IN = self.CLASS()
        IN.init()
        IN.arguments(('--hi',))
        IN.configure()
        with nt.assert_raises(SystemExit):
            IN.parse()
    
    def test_call_action(self):
        """.do()"""
        class TestCLI(self.CLASS):
            def do(self):
                self.do_done = True
                
        IN = TestCLI()
        IN.init()
        IN.arguments(tuple())
        IN.configure()
        IN.parse()
        IN.do()
        nt.ok_(IN.do_done)
        
    def test_kill(self):
        """.kill() with KeyboardInterrupt"""
        class TestCLI(self.CLASS):
            def do(self):
                raise KeyboardInterrupt
            
            def kill(self):
                self.killed = True
        
        IN = TestCLI()
        IN.init()
        IN.arguments(tuple())
        with nt.assert_raises(KeyboardInterrupt):
            IN.run()
        nt.ok_(IN.killed)
    
    def test_run(self):
        """.run()"""
        class TestCLI(self.CLASS):
            def do(self):
                self.do_done = True
        IN = TestCLI()
        IN.arguments(tuple())
        nt.eq_(IN.run(),0)

    