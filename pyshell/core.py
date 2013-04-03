# -*- coding: utf-8 -*-
# 
#  helpers.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-03-16.
#  Copyright 2013 Alexander Rudy. All rights reserved.
# 

import time
from collections import OrderedDict

__all__ = ['Typedkwargs','State','Stateful']

class Typedkwargs(object):
    """docstring for TypedKWArgs"""
    
    keywords = {}
    
    def _parse_keyword_args(self,kwargs,lookup):
        """docstring for _parse_keywords"""
        for key in self.keywords:
            if key in kwargs and kwargs.get(key) is not None:
                value = kwargs.get(key)
            elif key in lookup:
                value = lookup.get(key)
            else:
                value = self.keywords[key]()
            try:
                value = self.keywords[key](value)
            except Exception:
                pass
            if isinstance(self.keywords[key],type) and not isinstance(value,self.keywords[key]):
                raise ValueError("Invalid type for {keyword:s}: {type:s} expected {vtype:s}".format(
                    keyword = key, type=type(value), vtype=self.keywords[key]
                ))
            else:
                setattr(self,key,value)
            if key in kwargs:
                del kwargs[key]
        if kwargs.keys():
            raise ValueError("Unprocessed Keywords: {!r}".format(kwargs.keys()))
            
class State(OrderedDict):
    """Controls the state of a system."""
    
    

class Stateful(object):
    """docstring for Stateful"""
    def __init__(self):
        super(Stateful, self).__init__()
        self._state = State()
        
    @property
    def state(self):
        """The boolean dictionary defining the state of this system."""
        return { key : bool(value) for key,value in self._state.iteritems() }
        
    def set_state(self,state):
        """Set a state to the current time."""
        self._state[state] = time.clock()
        
    