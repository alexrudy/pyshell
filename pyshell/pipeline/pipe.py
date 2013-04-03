# -*- coding: utf-8 -*-
# 
#  pipe.py
#  pyshell
#  
#  Created by Jaberwocky on 2013-04-03.
#  Copyright 2013 Jaberwocky. All rights reserved.
# 
import time
import argparse
import re
import logging
from collections import OrderedDict

from .. import CLIEngine
from ..core import Stateful, State, Typedkwargs
from ..util import func_lineno

class Pipe(Stateful,Typedkwargs):
    """A basic pipe object."""
    
    keywords = {
        'exceptions' : tuple,
        'triggers' : list,
        'dependencies' : list,
        'replaces' : list,
        'optional' : bool,
        'include' : bool,
        'parent': str,
        'handle': lambda : (lambda a : a),
    }
    
    def __init__(self,action=lambda : None,name=None, description=None,help=None,module=None,**kwargs):
        super(Pipe, self).__init__()
        self.log = logging.getLogger(module if module is not None else self.__module__)
        self._name = name
        self._state = State.fromkeys(["initialized","included","primed","replaced","triggered","started","excepted","completed","finished"],False)
        self.do = action
        self._desc = description
        self._help = help
        self._parse_keyword_args(kwargs,vars(self.do))
        self.set_state("initialized")
    
    
    def run(self,dry=False):
        """This pipe will run the program here."""
        try:
            self.set_state("started")
            self.log.debug("Started pipe {name}".format(name=self.name))
            self.log.log(25,unicode(self.description))
            if not dry:
                self.do()
        except Exception:
            self.set_state("excepted")
            self.log.debug("Exception in pipe {name}".format(name=self.name))
            try:
                raise
            except self.exceptions as e:
                self.handle(e)
        else:
            self.set_state("completed")
            self.log.debug("Completed pipe {name}".format(name=self.name))
        finally:
            self.set_state("finished")
            self.log.debug("Finished pipe {name}".format(name=self.name))
            
    
    @property
    def arg(self):
        """The command line argument for this pipe"""
        return self.name.replace(" ","-").replace("_","-")
    
    @property
    def name(self):
        """Return the name of this stage, derived from the action."""
        if self._name is None:
            return getattr(self.do,'__func__',self.do).__name__
        else:
            return self._name
    
    @property
    def help(self):
        """Return the help string for this function"""
        if self._help is None:
            return u"pipe {:s}".format(self.name)
        elif self._help is False:
            return argparse.SUPPRESS
        elif isinstance(self._help,unicode):
            return self._help
        else:
            return unicode(self._help)
            
    @property
    def description(self):
        """Return the description for this item"""
        if self._desc is None and hasattr(self.do,'description'):
            return self.do.description
        elif self._desc is None and len(getattr(self.do,'__doc__','')):
             return self.do.__doc__
        elif not self._desc:
            return "Running {:s}".format(self.name)
        elif isinstance(self._desc,unicode):
            return self._desc
        else:
            return unicode(self._desc)
    
    
    def tree(self,pipes,level=0,dup=False):
        """Return the tree line."""
        if self.state["replaced"]:
            arrow = u"╎  "
            space = u" "
        elif self.state["triggered"] and self.state["primed"]:
            arrow = u"┌─>" if not dup else u"┌  "
            space = u" "
        elif self.state["included"]:
            arrow = u"┼─>" if not dup else u"┼  "
            space = u" "
        elif self.state["primed"]:
            arrow = u"└─>" if not dup else u"└  "
            space = u" "
            
        lines = []
        for pipe in reversed(pipes):
            if pipe.name in self.dependencies:
                if pipe.parent == self.name:
                    lines += pipe.tree(pipes,level+1,False)
                else:
                    lines += pipe.tree(pipes,level+1,True)
            if pipe.name == self.name:
                lines += [u"{left:30s}{desc:s}".format(
                            left = (space * level) + arrow + self.name,
                            desc = self.description,
                        )]
            if pipe.name in self.triggers:
                if pipe.parent == self.name:
                    lines += pipe.tree(pipes,level+1,False)
                else:
                    lines += pipe.tree(pipes,level+1,True)
        return lines
    
    
    @property
    def profile(self):
        """A profile of this timing object"""
        data = self.state
        if data["started"] and data["finished"]:
            data["processing time"] = self._state["finished"] - self._state["started"]
        elif data["started"]:
            data["processing time"] = time.clock() - self._state["started"]
        else:
            data["processsing time"] = 0
        return data
        