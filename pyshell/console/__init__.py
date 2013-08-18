# -*- coding: utf-8 -*-
# 
#  __init__.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-04-26.
#  Copyright 2013 Alexander Rudy. All rights reserved.
# 

try:
    from IPython.utils.coloransi import TermColors
except ImportError:
    from . import terminal
    HAVE_IPYTHON = False
else:
    HAVE_IPYTHON = True


__all__ = ['get_color']

def get_color(color):
    """Try to get colors!"""
    if HAVE_IPYTHON:
        return getattr(TermColors,color.capitalize(),TermColors.Normal)
    else:
        return getattr(terminal,color.upper(),terminal.NORMAL)
    
