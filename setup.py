# -*- coding: utf-8 -*-
# 
#  setup.py
#  pyshell
#  
#  Created by Alexander Rudy on 2012-09-29.
#  Copyright 2012 Alexander Rudy. All rights reserved.
# 

from distribute_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

from pyshell import version

setup(
    name = 'pyshell',
    version = version,
    packages = find_packages(exclude=['tests']),
    package_data = {'pyshell':['Defaults.yaml']},
    install_requires = ['distribute','PyYAML>=3.10'],
    test_suite = 'tests',
    author = 'Alexander Rudy',
    author_email = 'dev@alexrudy.org',
    entry_points = {
        'console_scripts' : ["BackUp = pyshell.backup:BackupEngine.script",
                            "PyPackage = pyshell.package:PyPackageEngine.script"]
    }
)