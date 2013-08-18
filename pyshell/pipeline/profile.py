# -*- coding: utf-8 -*-
# 
#  profile.py
#  pyshell
#  
#  Created by Jaberwocky on 2013-04-03.
#  Copyright 2013 Jaberwocky. All rights reserved.
# 

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)


from jinja2 import Environment, PackageLoader
from ..config import DottedConfiguration


class Profile(object):
    """A pipeline profile object"""
    def __init__(self,pipeline):
        super(Profile, self).__init__()
        self.pipeline = pipeline
        self.context = DottedConfiguration()
        self._templates = Environment(loader=PackageLoader('pyshell', 'templates'))
        
    @property
    def total_time(self):
        """docstring for total_time"""
        return sum([ item.profile["processing time"] for item in self.pipeline.call ])
        
    def to_context(self):
        """Gather the context used for this profile."""
        self.context["sequence"] = self.pipeline.call
        self.context["total"] = self.total_time
        self.context["name"] = self.pipeline.name
        return self.context
        
    def to_html(self,filename='profile.html'):
        """Return the HTML profile"""
        self._templates.get_template('profile.html').stream(**self.to_context()).dump(filename)
        
    def to_txt(self,filename='profile.txt'):
        """docstring for to_txt"""
        self._templates.get_template('profile.txt').stream(**self.to_context()).dump(filename)
        
    