#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
#  silly_pipeline.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-01-24.
#  Copyright 2013 Alexander Rudy. All rights reserved.
# 
from __future__ import division

from pyshell.pipeline import Pipeline
from pyshell.pipeline._oldhelp import *
import time


class SillyPipeline(Pipeline):
    """docstring for SillyPipeline"""
        
    supercfg = Pipeline.PYSHELL_LOGGING_STREAM
        
    defaultcfg = "silly_pipeline.yml"
        
    def init(self):
        """docstring for init"""
        super(SillyPipeline, self).init()
        self.collect()
        
    def stepA(self):
        """stepA"""
        pass
        
    @depends('stepA')
    def stepB(self):
        """stepB"""
        pass
        
        
    @include
    @depends('stepA','stepB')
    @triggers("stepD")
    def stepC(self):
        """stepC"""
        pass
        
    @triggers("stepE","stepF")
    def stepD(self):
        """stepD"""
        time.sleep(1)
        
    
    
    def stepE(self):
        """stepE"""
        pass
        
    @replaces("stepE")
    def stepF(self):
        """stepF"""
        pass


if __name__ == '__main__':
    SillyPipeline.script()