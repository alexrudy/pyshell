# -*- coding: utf-8 -*-
# 
#  helpers.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-03-16.
#  Copyright 2013 Alexander Rudy. All rights reserved.
# 

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)

import time
from collections import OrderedDict
from .config import MutableMappingBase

__all__ = ['Typedkwargs','State','Stateful','Struct','OneToOneMapping']

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
    pass
    

class Stateful(object):
    """A base class for objects which have some sort of state."""
    def __init__(self,*args,**kwargs):
        super(Stateful, self).__init__(*args,**kwargs)
        self._state = State()
        
    @property
    def state(self):
        """The boolean dictionary defining the state of this system."""
        return { key : bool(value) for key,value in self._state.iteritems() }
        
    @property
    def timing(self):
        """The dictionary of timing values for each state flag."""
        return self._state
        
    def set_state(self,state):
        """Set a state to the current time."""
        self._state[state] = time.time()
        
    def del_state(self,state):
        """docstring for del_state"""
        self._state[state] = False
        

class OneToOneMapping(MutableMappingBase):
    """A mapping that goes both ways. Looking up map[k] = v and map[v] = k works."""
    
    def __init__(self, *args, **kwargs):
        super(OneToOneMapping, self).__init__(*args, **kwargs)
        for k, v in self._store.items():
            self._store[v] = k
    
    def __setitem__(self, key, value):
        """Replace the normal setitem to do both directions."""
        self._store.__setitem__(key, value)
        self._store.__setitem__(value, key)
    
    def __delitem__(self, key):
        """Delete items in both directions"""
        self._store.__delitem__(self._store.pop(key))
        
class Struct(object):
    """A basic structure"""
    pass