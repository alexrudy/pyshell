# -*- coding: utf-8 -*-
# 
#  errors.py
#  pystellar
#  
#  Created by Alexander Rudy on 2012-10-29.
#  Copyright 2012 Alexander Rudy. All rights reserved.
# 


class CodedError(Exception):
    """Handles errors with this module's state."""
    def __init__(self,msg,code=0,**kwds):
        self.msg = msg
        self.code = code
        self.kwds = kwds
        
    def __str__(self):
        return u"%s:%d: %s" % (self.__class__.__name__,self.code,self.msg)