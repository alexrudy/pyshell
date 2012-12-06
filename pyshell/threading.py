# -*- coding: utf-8 -*-
# 
#  threading.py
#  pystellar
#  
#  Created by Jaberwocky on 2012-10-12.
#  Copyright 2012 Jaberwocky. All rights reserved.
# 
"""
:mod:`threading` - Thread Management
====================================

.. autoclass::
    ObjectThread
    :members:
    :inherited-members:
    
.. autoclass::
    ObjectsManager
    :members:
    :inherited-members:
    
Helper Classes
**************

    
.. autoclass::
    ObjectManager
    :members:
    
.. autoexception::
    ThreadStateError
    

"""
from __future__ import division

from StringIO import StringIO

import numpy as np
import scipy as sp

from pkg_resources import resource_filename
from warnings import warn

from multiprocessing import Queue, Process, Pool, Manager, Event, Lock, cpu_count, current_process
from Queue import Empty as QEmpty, Full as QFull
import logging
# Alex's modules
# from pyshell.config import DottedConfiguration

# Internal Modules
class CodedError(Exception):
    """Handles errors with this module's state."""
    def __init__(self,msg,code=0,**kwds):
        self.msg = msg
        self.code = code
        self.kwds = kwds
        
    def __str__(self):
        return u"%s:%d: %s" % (self.__class__.__name__,self.code,self.msg)


class ThreadStateError(CodedError):
    """Handles errors with this module's state."""
    
    codes = {
        2**1 : "Immutable thread pool",
        2**2 : "Subthread Error",
        2**3 : "Subthread Timeout",
    }
    
    def __init__(self,msg,code=0,thread=None):
        super(ThreadStateError, self).__init__(msg, code)
        self.thread = thread if thread is not None else '__main__'
        
    def __str__(self):
        return u"%s on %s: %s" % (self.__class__.__name__,self.thread,self.msg)
        

class ObjectManager(object):
    """A thread management object for single object threads"""
    def __init__(self,input_Q=None, output_Q=None, timeout=10, locking=False, lock=None, **kwargs):
        super(ObjectManager, self).__init__(**kwargs)
        self.input = Queue() if input_Q is None else input_Q
        self.output = Queue() if output_Q is None else output_Q
        self._timeout = timeout
        self._locking = locking
        if lock is None:
            self._lock = Lock()
        else:
            self._lock = lock
        self.hdr = {}
        self.hdr['pid'] = current_process().pid
    
    def __getattr__(self,attr):
        """Call a method on the underlying threaded object"""
        
        def method(*args,**kwargs):
            """A threaded method"""
            if self._locking:
                self._lock.acquire()
            self.input.put((self.hdr,attr,args,kwargs),timeout=self._timeout)
            
        return method
    
    @property
    def duplicator(self):
        """Arguments required to duplicate this manager"""
        return {
            "input_Q" : self.input,
            "output_Q": self.output,
            "timeout" : self._timeout,
            "locking" : self._locking,
            "lock" : self._lock
        }
    
    def retrieve(self,inputs=False,timeout=None):
        """Retrieve a return value off the top of the output queue"""
        timeout = self._timeout if timeout is None else timeout
        try:
            hdr,func,args,kwargs,rvalue = self.output.get(timeout=timeout)
        except QFull, QEmpty:
            raise ThreadStateError(code=2**3,msg="Subthread Ended")
        if self._locking:
            self._lock.release()
        if inputs:
            return func,args,kwargs,rvalue,hdr
        else:
            return rvalue
    
    def release(self,timeout=None):
        """Release a given lock, throwing away an outputs."""
        timeout = self._timeout if timeout is None else timeout
        try:
            hdr,func,args,kwargs,rvalue = self.output.get(timeout=timeout)
        except QFull, QEmpty:
            raise ThreadStateError(code=2**3,msg="Subthread Ended")
        if self._locking:
            self._lock.release()
        
    def clear(self):
        """Clear and join the queues"""
        self.output.put(None)
        self.input.put(None)

class ObjectThread(ObjectManager,Process):
    """docstring for ObjectThread"""
    def __init__(self, Oclass, iargs=(), ikwargs={},**kwargs):
        kwargs.setdefault("name",Oclass.__name__)
        super(ObjectThread, self).__init__(**kwargs)
        self.Oclass = Oclass
        self._args = iargs
        self._kwargs = ikwargs
    
    STOP = '..stop'
    
    def kill(self):
        return super(ObjectThread, self).terminate()
        
    
    def stop(self):
        """Send the thread stop signal."""
        self.input.put((self.hdr,self.STOP,None,None),timeout=self._timeout)
        self.clear()
        self.join()
    
    def run(self):
        """starts an opactiy thread which takes a queue of items."""
        O = self.Oclass(*self._args, **self._kwargs)
        done = False
        while not done:
            hdr, func, args, kwargs = self.input.get(timeout=self._timeout)
            if self.STOP == func:
                done = True
            else:
                try:
                    attr = getattr(O,func)
                    if callable(attr):
                        rvalue = attr(*args,**kwargs)
                    elif len(args)==0 and len(kwargs)==0:
                        rvalue = attr
                    elif len(args)==1 and len(kwargs)==0:
                        setattr(O,func,args)
                        rvalue = None
                    else:
                        raise AttributeError("Asked for attribute with arguments!")
                    if self._locking or rvalue is not None:
                        self.output.put((hdr,func,args,kwargs,rvalue),timeout=self._timeout)
                except QEmpty, QFull:
                    done = True
                except Exception as e:
                    done = True
                    raise #ThreadStateError(msg=str(e),code=2**2,thread=self.pid)

class ObjectPassthrough(ObjectThread):
    """An object which simply perfoms the passthrough to a thread."""
    def __init__(self, *args, **kwargs):
        self.nprocs = kwargs.pop('nprocs',0)
        super(ObjectPassthrough, self).__init__(*args, **kwargs)
    
    def start(self):
        """Starts this object"""
        self._started = True
        
    def retrieve(self,inputs=False,timeout=None):
        """Retrieve a return value off the top of the output queue"""
        timeout = self._timeout if timeout is None else timeout
        self.stop()
        self.run()
        try:
            hdr,func,args,kwargs,rvalue = self.output.get(timeout=timeout)
        except QEmpty, QFull:
            raise 
        if inputs:
            return func,args,kwargs,rvalue
        else:
            return rvalue
        
    def stop(self):
        """Send the thread stop signal."""
        self.input.put((self.hdr,self.STOP,None,None),timeout=self._timeout)
        
class ObjectsManager(ObjectManager):
    """A manager for handling many threaded objects which take from a single job queue and return to a single job queue.
    
    :param object Oclass: The class which will be instantiated in the new thread.
    :param args: Any positional arguments to be used upon instantiation of this class.
    :param kwargs: Any keyword arguments to be used upon instatiation of this class. Some values are reserved.
    :keyword nprocs: The number of threads to use from this manager. Defaults to `cpu_count()`.
    :keyword timeout: The number of seconds for any thread operation to timeout. Defualts to `10`.
    :keyword input_Q: This keyword will be used by the object to pass the input Queue.
    :keyword output_Q: This keyword will be used by the object to pass the output Queue.
    
    """
    def __init__(self, Oclass, iargs=(), ikwargs={}, nprocs=None, timeout=10, input_Q = None, output_Q = None):
        super(ObjectsManager, self).__init__()
        self.Oclass = Oclass
        self._args = iargs
        self._nprocs = cpu_count() if nprocs is None else nprocs
        self._kwargs = ikwargs
        self._started = False
        self.input = Queue() if input_Q is None else input_Q
        self.output = Queue() if output_Q is None else output_Q
        self._timeout = timeout
        self._procs = [ ObjectThread(self.Oclass,iargs=self._args,ikwargs=self._kwargs,input_Q=self.input, output_Q=self.output ) for i in xrange(self._nprocs) ]
        
    
    
    @property
    def started(self):
        return self._started
        
    def start(self):
        """docstring for fname"""
        if self.started:
            raise ThreadStateError("Thread pool already started",code=2**1)
        for proc in self._procs:
            proc.start()
        self._started = True
        
    def __getattr__(self,attr):
        """Call a method on the underlying threaded object"""
        
        def method(*args,**kwargs):
            """A threaded method"""
            self.input.put((self.hdr,attr,args,kwargs))
            
        return method
    
    @property
    def empty(self):
        """Lets us know if the output queue is empty"""
        return self.output.empty()
        
    def stop(self):
        """Send the thread stop signal."""
        if not self.started:
            raise ThreadStateError("Thread pool not started",code=2**1)
        for proc in self._procs:
            self.input.put((self.hdr,proc.STOP,None,None),timeout=self._timeout)
        for proc in self._procs:
            proc.join(timeout=self._timeout)
        self._started = False

    def terminate(self):
        """Terminate all attached threads."""
        

class EngineManager(ObjectsManager,Process):
    """Uses header values to handle directed requests and results."""
    def __init__(self,*args,**kwargs):
        super(EngineManager, self).__init__(*args,**kwargs)
        self.manager = Manager()
        self.results = self.manager.dict()
        self.block = Event()
        
    def retrieve(self,jid=None,inputs=False,timeout=None,block=True):
        """Retrieve a job given a jid"""
        if jid is None:
            jid = self.cjid
        if block:
            self.block.wait()
        hdr,func,args,kwargs,rvalue = self.results[jid]
        self.block.clear()
        if inputs:
            return func,args,kwargs,rvalue
        else:
            return rvalue
    
    def ready(self,jid):
        """Check if a job id is ready."""
        return jid in self.results
        
    
    def __getattr__(self,attr):
        """Call a method on the underlying threaded object"""
        
        def method(*args,**kwargs):
            """A threaded method"""
            jid = id((attr,args,kwargs))
            self.cjid = jid
            self.hdr["jid"] = jid
            self.input.put((self.hdr,attr,args,kwargs))
            return jid
        
        return method
        
    def start(self):
        """Start"""
        super(EngineManager, self).start()
        
    def run(self):
        """Run the subthread to move things off the output."""
        running = True
        while running:
            hdr,func,args,kwargs,rvalue = self.output.get()
            if "stop" in hdr:
                running = False
            else:
                self.results[hdr["jid"]] = (hdr,func,args,kwargs,rvalue)
                self.block.set()
        
    