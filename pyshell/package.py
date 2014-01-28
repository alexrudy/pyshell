# -*- coding: utf-8 -*-
# 
#  package.py
#  jaberwocky
#  
#  Created by Jaberwocky on 2012-10-16.
#  Copyright 2012 Jaberwocky. All rights reserved.
# 

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)
                        
import os, os.path, sys
import shutil
import logging
import datetime
import errno
from textwrap import fill, TextWrapper

from pkg_resources import resource_filename
from jinja2 import Environment, PackageLoader

from .subcommand import SCEngine, SCController
from .util import query_yes_no, query_string
from . import PYSHELL_LOGGING_STREAM

class PackageConfigError(Exception):
    """Package Configuration Error"""
    def __init__(self, msg):
        super(PackageConfigError, self).__init__()
        self.msg = msg
        
    def __str__(self):
        """Strigify"""
        return "Package Error: %s" % self.msg
        

class PyPackageBase(object):
    """docstring for PyPackageBase"""
    
    _desc = """Create new python packages using the setup.py convention with distutils. This tool will help you set up your python package."""
        
    @property
    def description(self):
        return fill(self._desc)
        
    @property
    def path(self):
        """Path to the working module."""
        return os.path.relpath(self.config["path"],self._cwd)
        
    @property
    def distname(self):
        """Name of the current distribution development"""
        return self.config["distname"]
        

class BaseSubEngine(PyPackageBase,SCEngine):
    """A base engine for use as a subcommand to PyPackageEngine"""
    def __init__(self, **kwargs):
        super(BaseSubEngine, self).__init__(**kwargs)
        self._kwargs = kwargs
        self._cwd = os.getcwd()
        self._templates = Environment(loader=PackageLoader('pyshell', 'templates'))
        self._creations = []
        
    def help(self,message,*args,**kwargs):
        """docstring for help"""
        tw = TextWrapper()
        tw.subsequent_indent = '    '
        self.log._log(logging.HELP,tw.fill(message),args,**kwargs)
        
    def create_dir(self,directory):
        """Soft directory creation with proper logging"""
        if os.path.exists(directory) and os.path.isdir(directory):
            self.log.debug("Directory '%s' already exists" % directory)
        elif os.path.exists(directory):
            raise PackageConfigError("Path '%s' does not appear to be a directory!" % directory)
        else:
            os.mkdir(directory)
            self.log.debug("Created directory '%s'" % (directory))
            return True
        return False
            
    def check_file(self,filepath):
        """docstring for check_file"""
        if os.path.exists(filepath):
            self.log.debug("File '%s' already exists" % filepath)
            return False
        return True
        
        
class PackageEngine(BaseSubEngine):
    """An engine for creating new pacakges"""
    
    _help = "Create a new pacakge"
    
    command = "dist"
    
    def __init__(self):
        super(PackageEngine, self).__init__(help=self._help)
        
    def init(self):
        """Set up the parsing for this command."""
        super(PackageEngine, self).init()
        self._parser.add_argument('--no-distribute',action='store_false',dest='distribute',help="Skip the distribute_setup.py file")
        self._parser.add_argument('--no-setup',action='store_false',dest='setup',help="Skip the setup.py file (NOT RECOMMENDED)")
        self._parser.add_argument('--no-test-module',action='store_false',dest='use_test_module',help="Do not include a nosetests module")
        self._parser.add_argument('--test-module',nargs=1,default='tests',metavar='tests',help="Set the test module name")
        self._parser.add_argument('--requirements',nargs='+',default='',metavar='PyPackage>=0.3',help="Requirements to be added to setup.py")
        self._parser.add_argument('--no-data-directory',action='store_false',dest='use_datadir',help="Skip the data directories")
        self._parser.add_argument('--data-directory',nargs=1,default='data/',metavar='data/',dest='datadir',help="Set the directory module name")
        
    def configure(self):
        """Configure this subengine"""
        super(PackageEngine, self).configure()
        self._parser.add_argument('packages',nargs='+',metavar='package',help="Packages to create")
        self._config["tests"] = self._opts.test_module
        self._config["path"] = os.path.normpath(self._opts.destination)
        self._config["distname"] = self._config["path"].split("/")[-1]
        self._config["template.name"] = self.distname
        self._config["template.date"] = datetime.date.today().isoformat()
        self._config["template.exclude"] = self.config.get("template.exclude",[])
        
    def do(self):
        """Start the package creation process"""
        self.make_distribution()
        self.get_metadata()
        try:
            self.make_packages()
            self.make_tests()
            self.make_data_directory()
            self.make_setup()
        except IOError as e:
            if e.errno == errno.EACCES:
                sys.stdout.write("Permission denied!\n")
            raise
        
    def make_distribution(self):
        """Create the distribution"""
        self.log.info("This will make a new python distribution called '%(distname)s' in" % self.config)
        self.log.info(" '%(path)s/'" % self.config)
        self.help("Distributions are groups of python modules which can be installed by a single 'setup.py' script. Multiple modules can be contained within a distribution. Each distribution can have dependencies on other distributions (such as 'numpy'). The 'setup.py' script for each distribution can also be used to install command line scripts.")
        if not query_yes_no("Create distribution '%(distname)s'?" % self.config):
            print("Cancelling distribution Creation")
            sys.exit(0)
        self.create_dir(self.path)
        if not os.path.isdir(self.path) or not os.access(self.path,os.X_OK):
            raise PackageConfigError("Can't access distribution directory '%s'" % self.path)
        self.log.info("Created distribution '%(distname)s'" % self.config)
        
    def get_metadata(self):
        """Ask the user for missing pieces of metadata"""
        self.log.debug("Gathering 'setup.py' Metadata")
        self.help("Metadata is used to provide information to the 'setup.py' script and to other default files created for each distribution, such as the README and various __init__.py files.")
        self._config["template.author"] = query_string("Author Name",default=self.config.get("template.author","Jaberwocky"))
        self._config["template.email"]  = query_string("Author Email",default=self.config.get("template.email","jab@erwo.ky"))
        self.log.debug("Setting dependencies")
        self.help("Dependencies are python packages, generally available from pypi (or otherwise already installed) which are required for the use of this distribution. The name provided should be the pypi name. Version numbers provided will be the minimum version, although more complex version numbering can be set in 'setup.py' if you wish. The package 'distribute' will be added to the dependencies list to ensure compatiblity with python's distutils")
        dependencies = self.config.get('template.dependencies',[])
        dependencies += ['distribute']
        dndep = "0"
        while True:
            ndeps = int(query_string("How many dependencies does the '%s' distribution have?" % self.distname,default=dndep))
            for n in range(ndeps):
                dep = query_string("Dependency",default="package")
                ver = query_string("Minimum Version",default="")
                if ver == "":
                    dependencies.append("%s" % dep)
                else:
                    dependencies.append("%s>=%s" % (dep,ver))
            if not query_yes_no("Any more dependencies?",default="no"):
                break
            dndep = "1"
        self._config["template.dependencies"] = dependencies
        
    
    def make_packages(self):
        """Make module directories requested"""
        for package in self._opts.packages:
            package_path = os.path.normpath("%s/%s" % (self.path,package))
            self.log.info("Creating module %s" % package)
            if os.path.exists(package_path):
                self.log.debug("Package %s already exists" % package)
            else:
                os.mkdir(package_path)
                self.log.debug("Created directory '%s'" % (package_path))
            init_filename = os.path.normpath("%(path)s/%(package)s/__init__.py" % dict(path=self.path,package=package))
            if os.path.exists(init_filename):
                self.log.debug("'%s' already exists" % init_filename)
            else:
                self.log.debug("Creating '%s'" % init_filename)
                self._templates.get_template('__init__.py.txt').stream(package=package,**self.config["template"]).dump(init_filename)
                
    
    def make_tests(self):
        """docstring for make_tests"""
        if not (self._opts.use_test_module and query_yes_no("Create unittest module '%s'?" % self.config["tests"])):
            return
        test_path = os.path.normpath("%s/%s" % (self.path,self.config["tests"]))
        if os.path.isdir(test_path):
            self.log.debug("Unittest module '%s' already exists" % self.config["tests"])
        else:
            os.mkdir(test_path)
            self._config["template.exclude"] += [self.config["tests"]]
            self.log.debug("Created directory '%s'" % test_path)
        init_filename = os.path.normpath("%(path)s/%(package)s/__init__.py" % dict(path=self.path,package=self.config["tests"]))
        if os.path.exists(init_filename):
            self.log.debug("'__init__.py' already exists")
        else:
            self.log.debug("Creating '%s'" % init_filename)
            self._templates.get_template('test__init__.py.txt').stream(package=self.config["tests"],**self.config["template"]).dump(init_filename)
        for package in self._opts.packages:
            mod_filename = os.path.normpath("%s/test_%s.py" % (test_path,package))
            self.log.debug("Creating '%s'" % mod_filename)
            self._templates.get_template('tests__module__.py.txt').stream(package=package,**self.config["template"]).dump(mod_filename)
        self.log.info("Created unittest module '%s'" % self.config["tests"])
        
        
    def make_setup(self):
        """docstring for make_setup"""
        if not (self._opts.setup and query_yes_no("Create 'setup.py' file?")):
            return
        setup_filename = os.path.normpath("%s/setup.py" % self.path)
        distribute_filename = os.path.normpath("%s/distribute_setup.py" % self.path)
        if os.path.exists(setup_filename):
            self.log.debug("'%s' already exists" % setup_filename)
        else:
            self.log.debug("Creating %s" % setup_filename)
            self._templates.get_template('setup.py.txt').stream(**self.config["template"]).dump(setup_filename)
        if os.path.exists(distribute_filename):
            self.log.debug("'%s' already exists" % distribute_filename)
        else:
            self.log.debug("Creating %s" % distribute_filename)
            shutil.copy(resource_filename(__name__,'data/distribute_setup.py'),distribute_filename)
        
    def make_data_directory(self):
        """Create a data directory"""
        if not self._opts.use_datadir:
            return
        self._config['template.package_data'] = self.config.get("template.package_data",{})
        for package in self._opts.packages:
            if not query_yes_no("Create a directory to hold non-python files associated with the '%s' package?" % package):
                return
            data_dir = os.path.normpath("%s/%s/%s" % (self.path,package,self._opts.datadir))
            data_dir_short = os.path.normpath("%s/%s/*" % (package,self._opts.datadir))
            if os.path.exists(data_dir):
                self.log.debug("Data directory '%s' already exists" % data_dir)
            else:
                self.log.debug("Creating data directory '%s' in package '%s'." % (self._opts.datadir,package))
                os.mkdir(data_dir)
            self._config["template.package_data"][package] = [data_dir_short]

class PyPackageEngine(SCController,PyPackageBase):
    """An engine for the creation of python packages"""
    
    defaultcfg = "Package.yml"
    
    supercfg = PYSHELL_LOGGING_STREAM
    
    _subEngines = [ PackageEngine, ]
    
    def __init__(self):
        super(PyPackageEngine, self).__init__()
        logging.addLevelName(5,'HELP')
        logging.HELP = 5
        self._cwd = os.getcwd()
        
    def init(self):
        """docstring for init"""
        super(PyPackageEngine, self).init()
        self._parser.add_argument('-n','--dry-run',action='store_false',dest='run',help="Print what would be done, but don't copy")
        self._parser.add_argument('--destination',metavar='/path/to/',nargs=1,default=self._cwd,help='Set the destination for this module. Defaults to here.')
        self._parser.add_argument('-v','--verbose',action='store_true',help="Print help messages along the way.")
        
        
        
    def configure(self):
        """Configure the package creator"""
        self._config["template.author"] = os.environ['LOGNAME']
        super(PyPackageEngine, self).configure()
        self.log.setLevel(logging.HELP if self._opts.verbose else logging.WARNING)

        