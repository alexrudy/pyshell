# -*- coding: utf-8 -*-
# 
#  setup.py
#  pyshell
#  
#  Created by Alexander Rudy on 2012-09-29.
#  Copyright 2012 Alexander Rudy. All rights reserved.
# 

try:
    import setuptools
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()

from setuptools import setup, find_packages

from pyshell import version

setup(
    name = 'pyshell',
    version = version,
    packages = find_packages(exclude=['tests']),
    package_data = {'pyshell':['*.yml','templates/*']},
    install_requires = ['distribute','PyYAML>=3.10','jinja2>2.0', 'six>=1.4.1'],
    test_suite = 'tests',
    tests_require = ['nose','nose-capturestderr'],
    author = 'Alexander Rudy',
    author_email = 'dev@alexrudy.org',
    url = "http://github.com/alexrudy/pyshell",
    zip_safe = True,
    entry_points = {
        'console_scripts' : ["BackUp = pyshell.backup:BackupEngine.script",
                            "PyPackage = pyshell.package:PyPackageEngine.script",
                            "BumpVersion = pyshell.bump_version:VersionBumper.script"],
        'nose.plugins.0.10': [
                    'postmortem = pyshell.nosetests.postmortem:PostMortemPlugin',
                    ]
    }
)