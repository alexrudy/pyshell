# -*- coding: utf-8 -*-
# 
#  postmortem.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-08-16.
#  Copyright 2013 Alexander Rudy. All rights reserved.
# 
"""
:mod:`postmortem` – A postmortem debugging tool for nosetests.
==============================================================

This plugin provides a simple way to save data files (specifically .npy files) after a test has failed in nosetests, and to delete those files when the test passes. I use it for simple debugging, to save data from failing tests.

To use the postmortem plugin, you must enable it with the command-line option ``--with-postmortem``. Then, it will inspect test instances for a ``POST_SAVE`` variable. The plugin uses class isntances as a way to save the variables after the test function has finished. It does nothing for non-class instance.

The ``POST_SAVE`` variable should be a list containing tuples. The tuples are pairs of `(data, filename)` which will be saved. Filenames which end with ``.npy`` will be saved using ``np.save()``. ``.dat`` will be saved with ``np.savetxt()``. Other extensions will be written as strings to text files.

A list of all the files saved will be saved using the format ``<test_id>.txt`` in the same folder. This list is used by :class:`PostMortemScript` to load saved files.

:class:`PostMortemScript` - A CLI for inspecting post-mortem data
-----------------------------------------------------------------

.. autoclass:: PostMortemScript
    :members:
    
:class:`PostMortemPlugin` - Implementation of the :mod:`nose` plugin
--------------------------------------------------------------------

.. autoclass:: PostMortemPlugin
    :members:

"""


from __future__ import (absolute_import, unicode_literals, division,
                        print_function)

from nose.plugins import Plugin
from nose.case import MethodTestCase

import os, os.path
import glob
import sys

import numpy as np

from ..base import CLIEngine
from ..util import remove
from ..loggers import getLogger
from ..config import DottedConfiguration

class PostMortemPlugin(Plugin):
    """A plugin to perform actions after a test has failed, usually saving failures."""
    
    name = 'postmortem'
    
    def options(self, parser, env=None):
        """Set up plugin options"""
        if env is None:
            env = os.environ
        super(PostMortemPlugin, self).options(parser, env=env)
        
    def configure(self, options, conf):
        """Set up configuration"""
        super(PostMortemPlugin, self).configure(options, conf)
        if not self.enabled:
            return
        self.log = getLogger("nose.plugins.postmortem")
        
    def addFailure(self, test, err):
        """Post Mortem Failure information"""
        if not isinstance(test, MethodTestCase):
            return
        if hasattr(test.test.inst,'POST_SAVE'):
            self.post_dir = os.path.join(os.path.dirname(sys.modules[test.test.inst.__module__].__file__),"postmortem","data")
            if not os.path.exists(self.post_dir):
                os.makedirs(self.post_dir)
            filenames = [ self.save(item, filename) for item, filename in test.test.inst.POST_SAVE ]
            datafile = os.path.join(self.post_dir,test.id()+'.txt')
            with open(datafile, 'w') as stream:
                stream.write("\n".join(filenames))
        
    
    def addSuccess(self, test):
        """Clean up PostMortem Failure information"""
        if not isinstance(test, MethodTestCase):
            return
        if hasattr(test.test.inst,'POST_SAVE'):
            self.post_dir = os.path.join(os.path.dirname(sys.modules[test.test.inst.__module__].__file__),"postmortem","data")
            filelist = os.path.join(self.post_dir,test.id()+'.txt')
            if os.path.exists(filelist):
                with open(filelist, 'r') as stream:
                    files = stream.read().splitlines()
                for filename in files:
                    remove(filename)
            for item, filename in test.test.inst.POST_SAVE:
                remove(filename)
            remove(filelist)
    
    def save(self, item, filename):
        """Save a particular item."""
        filepath = os.path.join(self.post_dir,filename)
        try:
            if isinstance(item, np.ndarray):
                if filename.endswith(".npy"):
                    np.save(filepath, item)
                elif filename.endswith(".dat"):
                    np.savetxt(filepath, item)
            elif isinstance(item, basestring):
                with open(filepath,'w') as stream:
                    stream.write(item)
        except Exception as e:
            self.log.error("File %s save Error: %r", filename, e)
            return None
        else:
            self.log.info("Saved %s.", filepath)
            return filepath
            
    def clean(self, item, filename):
        """Clean up postmortem files"""
        filepath = os.path.join(self.post_dir,filename)
        remove(filepath)
        
class PostMortemScript(CLIEngine):
    """
    A script for managing post-mortem data.
    
    Set the class variables ``test_ids`` or ``module_ids`` to load test data. Then access test data during the :func:`do` method using the ``test_data`` configuration object.
    """
    
    defaultcfg = False
    
    test_ids = []
    """The test IDs to search for in the postmortem area."""
    module_ids = []
    """The module IDs to search for in the postmortem area. Module IDs search for any test which matches ``<module>.*.txt`` ."""
    
    test_data = None
    """The data loaded for this test. A dictionary mapping file ids to data. The file id is just ``test_id + filename``"""
    
    def init(self):
        """Initialize variables!"""
        self.test_data = DottedConfiguration()
    
    def after_configure(self):
        """Find and ready all of the relevant filenames."""
        self.config.setdefault("directory",os.path.join("tests","postmortem","data"))
        for test_id in self.test_ids:
            self.load_by_test_id(test_id)
        for module_id in self.module_ids:
            tests = self.find_tests(module_id)
            for test_id in tests:
                self.load_by_test_id(test_id)
        
    def find_tests(self,modulename):
        """Find tests"""
        tests = glob.glob(os.path.join(self.config["directory"],"{module:s}.*.txt".format(module=module_id)))
        return [ os.path.splitext(os.path.basename(test))[0] for test in tests ]
        
    def file_id(self, test_id, filename):
        """Make a file ID from a test ID and a filename."""
        return test_id + "." + os.path.splitext(os.path.basename(file))[0]
        
    def load_by_test_id(self, test_id):
        """Load the relevant files by test id."""
        filename = os.path.join(self.post_dir,test_id+".txt")
        with open(filename,'r') as stream:
            files = stream.read().splitlines()
        for file in files:
            self.load(test_id, file)
            
    def load(self, test_id, file):
        """Load a single test file."""
        try:
            if os.path.exists(file):
                file_id = self.file_id(test_id, file)
                if file.endswith(".npy"):
                    self.test_data[file_id] = np.load(file)
                elif file.endswidth(".dat"):
                    self.test_data[file_id] = np.loadtxt(file)
                else:
                    with open(file, 'r') as stream:
                        self.test_data[file_id] = stream.read()
        except IOError as e:
            self.log.error("IOError with file %s: %r", file, e)
    
