# -*- coding: utf-8 -*-
# 
#  progressbar.py
#  AstroObject
#  
#  Created by Alexander Rudy on 2012-05-08.
#  Copyright 2012 Alexander Rudy. All rights reserved.
# 
from __future__ import (absolute_import, unicode_literals, division,
                        print_function)

"""
:mod:`util.pbar` – Colored progressbar functions to extend the progressbar module
---------------------------------------------------------------------------------

This module contains extensions to the progressbar module (<http://pypi.python.org/pypi/progressbar/2.2>)

.. autoclass::
    ProgressBar
    :members:
    :inherited-members:
    
.. autoclass::
    ColorBar
    :members:
    :inherited-members:

"""
import progressbar

import string
from . import terminal

from progressbar import *


class ProgressBar(progressbar.ProgressBar):
    def update(self, value=None):
        """Updates the ProgressBar to a new value. Monkey Patch edition"""

        if value is not None and value is not progressbar.UnknownLength:
            if (self.maxval is not progressbar.UnknownLength
                and not 0 <= value <= self.maxval):

                raise ValueError('Value out of range')

            self.currval = value


        if not self._need_update(): return
        if self.start_time is None:
            raise RuntimeError('You must call "start" before calling "update"')

        now = time.time()
        self.seconds_elapsed = now - self.start_time
        self.next_update = self.currval + self.update_interval
        if getattr(self,'_lines',0) > 0:
            self.fd.write(self._lines * (terminal.UP + terminal.BOL + terminal.CLEAR_EOL))
        line = self._format_line() + "\n"
        self.fd.write(line)
        self.fd.flush()
        setattr(self,'_lines',len(line.splitlines()))
        self.last_update_time = now
        
    def finish(self):
        """Puts the progress bar in a finished state"""
        super(ProgressBar,self).finish()
        self.fd.write(self._lines * (terminal.UP + terminal.BOL + terminal.CLEAR_EOL))
        
class ColorBar(progressbar.Bar):
    'A progress bar which stretches to fill the line.'
    
    def __init__(self, marker='█', left='|', right='|', fill=' ',
                 fill_left=True, color="green"):
        '''Creates a customizable progress bar.

        marker - string or updatable object to use as a marker
        left - string or updatable object to use as a left border
        right - string or updatable object to use as a right border
        fill - character to use for the empty part of the progress bar
        fill_left - whether to fill from the left or the right
        '''
        self.marker = marker
        self.left = left
        self.right = right
        self.fill = fill
        self.fill_left = fill_left
        self.color = getattr(terminal,color.upper(),terminal.NORMAL)
        self.nocolor = terminal.NORMAL


    def update(self, pbar, width):
        'Updates the progress bar and its subcomponents'

        left, marked, right, color, nocolor = (progressbar.format_updatable(i, pbar) for i in
                               (self.left, self.marker, self.right, self.color, self.nocolor))
        width -= len(left) + len(right)
        itemw = len(self.marker)
        # Marked must *always* have length of 1
        if pbar.maxval:
          marked *= int(pbar.currval / pbar.maxval * width / itemw) 
        else:
          marked = ''
        if self.fill_left:            
            return '%s%s%s%s%s' % (color,left, marked.ljust(width, self.fill), right, nocolor)
        else:
            return '%s%s%s%s%s' % (color,left, marked.rjust(width, self.fill), right, nocolor)

