# -*- coding: utf-8 -*-
# 
#  test_yaml.py
#  pyshell
#  
#  Created by Jaberwocky on 2013-11-15.
#  Copyright 2013 Jaberwocky. All rights reserved.
# 

from __future__ import (absolute_import, unicode_literals, division, print_function)

import yaml
import pyshell.yaml as ps_yaml
from pkg_resources import resource_filename
import nose.tools as nt
import os
import collections
from six.moves import cStringIO as StringIO
import six

class test_yaml(object):
    """pyshell.yaml"""
    
    def setup(self):
        self.test_dict_A = {"Hi":{"A.py.p":1,"B":2,"D":[1,2],"E.py.p":{"F":"G"}},}
        self.test_dict_B = {"Hi":{"A.py.p":3,"C":4,"D":[3,4],"E.py.p":{"F":"G"}},}
        self.test_dict_C = {"Hi":{"A.py.p":3,"B":2,"C":4,"D":[3,4],"E.py.p":{"F":"G"}},} # Should be a merge of A and B
        self.test_dict_D = {"Hi":{"A.py.p":3,"B":2,"C":4,"D":[1,2,3,4],"E.py.p":{"F":"G"}},} # Should be a merge of A and B with a sequence
        self.test_dict_E = {"Hi.A.py.p":3,"Hi.B":2,"Hi.C":4,"Hi.D":[1,2,3,4],"Hi.E.py.p.F":"G"} # Should be a flattening of D
        self.test_dict_F = {"Hi":{"A":{"py":{"p":3}},"B":2,"C":4,"D":[1,2,3,4],"E":{"py":{"p":{"F":"G"}}}},} # Should be an expansion of D
    
    def test_roundtrip_keys(self):
        """Ensure YAML dumping is roundtrip key compatible"""
        data = yaml.dump(self.test_dict_A, Dumper=ps_yaml.UnicodeDumper)
        test_A = yaml.load(data, Loader=ps_yaml.UnicodeLoader)
        for key in test_A.keys():
            nt.ok_(isinstance(key, six.text_type),"Key was not UNICODE! {}".format(type(key)))
    
    def test_roundtrip_order(self):
        """Test the order of everything."""
        test_A = collections.OrderedDict(self.test_dict_A)
        order = test_A.keys()
        data = yaml.dump(test_A, Dumper=ps_yaml.OrderedDictSafeDumper)
        test_B = yaml.load(data, Loader=ps_yaml.OrderedDictLoader)
        nt.ok_(test_A.keys() == test_B.keys())
        