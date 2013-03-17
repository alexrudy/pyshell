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

from pyshell.pipeline2 import Pipeline
from pyshell.pipelinehelp import *


class SillyPipeline(Pipeline):
    """docstring for SillyPipeline"""
        
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
        """docstring for stepD"""
        pass
    
    
    def stepE(self):
        """docstring for stepE"""
        pass
        
    @replaces("stepE")
    def stepF(self):
        """docstring for stepF"""
        pass


if __name__ == '__main__':
    SillyPipeline.script()