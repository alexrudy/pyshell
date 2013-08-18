#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)


import pyshell


class maintest(pyshell.CLIEngine):
    """Test for the main module file variables"""
    
    modes = {
        "1" : "pyshell.util",
        "2" : "IPython.core.debugger",
        "3" : "IPython.core.ultratb",
    }
    
    defaultcfg = False
    
    def after_configure(self):
        """Set command line arguments"""
        self.parser.add_argument('mode',choices=self.modes.values()+self.modes.keys())
    
    def do(self):
        """Run the tests"""
        mode = self.opts.mode
        if mode in self.modes.keys():
            mode = self.modes[mode]
        print("Mode: '%s'" % mode)
        import sys
        print("Original Value of __file__: %r" % sys.modules['__main__'].__file__)
        _main = sys.modules['__main__']

        if mode == "pyshell.util":
            import pyshell.util
            pyshell.util.ipydb()
        elif mode == "IPython.core.debugger":
            import IPython.core.debugger
            IPython.core.debugger.Pdb()
        elif mode == "IPython.core.ultratb":
            import IPython.core.ultratb
            sys.excepthook = IPython.core.ultratb.FormattedTB(mode='Verbose',color_scheme='Linux', call_pdb=1)

        try:
            print("New Value of __file__: %r" % sys.modules['__main__'].__file__)
        except AttributeError:
            print("__file__ no longer exists:")
            print(dir(sys.modules['__main__']))
            print(sys.modules['__main__'].__doc__)

        sys.modules['__main__'] = _main
        try:
            print("Restored Value of __file__: %r" % sys.modules['__main__'].__file__)
        except AttributeError:
            print("__file__ no longer exists:")
            print(dir(sys.modules['__main__']))
            print(sys.modules['__main__'].__doc__)

if __name__ == '__main__':
    maintest.script()