#!/usr/bin/env python
# -*- coding: utf-8 -*-
mode = "pyshell.util"
import sys
print "Original Value of __file__: %r" % sys.modules['__main__'].__file__
_main = sys.modules['__main__']

if mode = "pyshell.util":
    import pyshell.util
    pyshell.util.ipydb()
elif mode = "IPython.core.debugger":
    import IPython.core.debugger
    IPython.core.debugger.Pdb()
elif mode = "IPython.core.ultratb":
    import IPython.core.ultratb
    sys.excepthook = IPython.core.ultratb.FormattedTB(mode='Verbose',color_scheme='Linux', call_pdb=1)

try:
    print "New Value of __file__: %r" % sys.modules['__main__'].__file__
except AttributeError:
    print "__file__ no longer exists:"
    print dir(sys.modules['__main__'])
    print sys.modules['__main__'].__doc__

sys.modules['__main__'] = _main
try:
    print "Restored Value of __file__: %r" % sys.modules['__main__'].__file__
except AttributeError:
    print "__file__ no longer exists:"
    print dir(sys.modules['__main__'])
    print sys.modules['__main__'].__doc__
