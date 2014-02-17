# -*- coding: utf-8 -*-
# 
#  fix_console_scripts.py
#  pyshell
#  
#  Created by Alexander Rudy on 2014-02-16.
#  Copyright 2014 Alexander Rudy. All rights reserved.
# 
"""
This module fixes the broken 'develop' mode console scripts in setuptools.

"""

from ..util import apply_monkey_patch
import textwrap


def install_wrapper_scripts(self, dist):
    "Fixed function to respect the executable set as an option."
    from setuptools.command.easy_install import sys_executable
    from setuptools.command.easy_install import get_script_args
    
    bs_cmd = self.get_finalized_command('build_scripts')
    executable = getattr(bs_cmd,'executable',sys_executable)
    
    if not self.exclude_scripts:
        for args in get_script_args(dist, executable):
            self.write_script(*args)
            

def get_script_header(script_text, executable=None, wininst=False):
    """Fix get_script_header to use virtualenvironments."""
    if executable is None:
        from setuptools.command.easy_install import sys_executable
        executable = sys_executable
    from setuptools.command.easy_install import _original_get_script_header
    header = _original_get_script_header(script_text, executable, wininst)
    
    environment_start = textwrap.dedent("""
    # If we are in a virtual environment, let's activate it.
    import os, os.path
    if "VIRTUAL_ENV" in os.environ:
        activate_this = os.path.join(os.environ["VIRTUAL_ENV"],'bin/activate_this.py')
        execfile(activate_this, dict(__file__=activate_this))
    
    """)
    return header + environment_start
    


def monkey_patch_setuptools():
    """Monkey-patches setuptools to respect interpreter options"""
    from setuptools.command.easy_install import easy_install as easy_install_cmd
    from setuptools.command import easy_install as easy_install_mod
    apply_monkey_patch(easy_install_cmd, install_wrapper_scripts)
    apply_monkey_patch(easy_install_mod, get_script_header)
    
