# -*- coding: utf-8 -*-
# 
#  test_mapping.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-11-13.
#  Copyright 2013 Alexander Rudy. All rights reserved.
# 
from __future__ import (absolute_import, unicode_literals, division,
                        print_function)

import yaml
import pyshell.mapping as mapping
from pkg_resources import resource_filename
import nose.tools as nt
import os
from six.moves import cStringIO as StringIO

class test_config(object):
    """pyshell.config"""
    def setup(self):
        self.test_dict_A = {"Hi":{"A.py.p":1,"B":2,"D":[1,2],"E.py.p":{"F":"G"}},}
        self.test_dict_B = {"Hi":{"A.py.p":3,"C":4,"D":[3,4],"E.py.p":{"F":"G"}},}
        self.test_dict_C = {"Hi":{"A.py.p":3,"B":2,"C":4,"D":[3,4],"E.py.p":{"F":"G"}},} # Should be a merge of A and B
        self.test_dict_D = {"Hi":{"A.py.p":3,"B":2,"C":4,"D":[1,2,3,4],"E.py.p":{"F":"G"}},} # Should be a merge of A and B with a sequence
        self.test_dict_E = {"Hi.A.py.p":3,"Hi.B":2,"Hi.C":4,"Hi.D":[1,2,3,4],"Hi.E.py.p.F":"G"} # Should be a flattening of D
        self.test_dict_F = {"Hi":{"A":{"py":{"p":3}},"B":2,"C":4,"D":[1,2,3,4],"E":{"py":{"p":{"F":"G"}}}},} # Should be an expansion of D
    
    def test_reformat(self):
        """reformat(d, nt)"""
        class nft(dict):
            pass
        
        rft = mapping.reformat(self.test_dict_C, nft)
        nt.ok_(isinstance(rft, nft))
        nt.ok_(isinstance(rft["Hi"], nft))
        nt.ok_(isinstance(rft["Hi"]["E.py.p"], nft))
        nt.assert_false(isinstance(self.test_dict_C, nft))
    
    def test_deepmerge(self):
        """deepmerge(d, u, s)"""
        res = mapping.deepmerge(self.test_dict_A, self.test_dict_B, dict)
        nt.eq_(self.test_dict_A, self.test_dict_C)
        nt.eq_(res, self.test_dict_C)
    
    def test_deepmerge_ip(self):
        """deepmerge(d, u, s, inplace=False)"""
        res = mapping.deepmerge(self.test_dict_A, self.test_dict_B, dict, inplace=False)
        nt.assert_not_equal(self.test_dict_A, self.test_dict_C)
        nt.eq_(res,self.test_dict_C)
    
    def test_deepmerge_i(self):
        """deepmerge(d, u, s, invert=True)"""
        res = mapping.deepmerge(self.test_dict_B, self.test_dict_A, dict, invert=True)
        nt.eq_(self.test_dict_B, self.test_dict_C)
        nt.eq_(res, self.test_dict_C)
    
    def test_deepmerge_ip_i(self):
        """deepmerge(d, u, s, invert=True, inplace=False)"""
        res = mapping.deepmerge(self.test_dict_B, self.test_dict_A, dict, invert=True, inplace=False)
        nt.assert_not_equal(self.test_dict_B, self.test_dict_C)
        nt.eq_(res, self.test_dict_C)
    
    def test_advdeepmerge(self):
        """advanceddeepmerge(d, u, s)"""
        res = mapping.advanceddeepmerge(self.test_dict_A, self.test_dict_B, dict)
        nt.eq_(self.test_dict_A, self.test_dict_D)
        nt.eq_(res, self.test_dict_D)
    
    def test_advdeepmerge_ip_(self):
        """advanceddeepmerge(d, u, s, inplace=False)"""
        res = mapping.advanceddeepmerge(self.test_dict_A, self.test_dict_B, dict, inplace=False)
        nt.assert_not_equal(self.test_dict_A, self.test_dict_D)
        nt.eq_(res, self.test_dict_D)
    
    def test_advdeepmerge_i(self):
        """advanceddeepmerge(d, u, s, invert=True)"""
        res = mapping.advanceddeepmerge(self.test_dict_B, self.test_dict_A, dict, invert=True)
        nt.eq_(self.test_dict_B, self.test_dict_D)
        nt.eq_(res, self.test_dict_D)
        
    def test_advdeepmerge_ip_i(self):
        """advanceddeepmerge(d, u, s, invert=True, inplace=False)"""
        res = mapping.advanceddeepmerge(self.test_dict_B, self.test_dict_A, dict, invert=True, inplace=False)
        nt.assert_not_equal(self.test_dict_B, self.test_dict_D)
        nt.eq_(res, self.test_dict_D)
        
    def test_flatten(self):
        """flatten(d)"""
        res = mapping.flatten(self.test_dict_D)
        nt.eq_(res, self.test_dict_E)
        res = mapping.flatten(self.test_dict_E)
        nt.eq_(res, self.test_dict_E)
        
    def test_expand(self):
        """expand(d)"""
        res = mapping.expand(self.test_dict_E)
        nt.eq_(res, self.test_dict_F)
        res = mapping.expand(self.test_dict_D)
        nt.eq_(res, self.test_dict_F)
        res = mapping.expand(self.test_dict_F)
        nt.eq_(res, self.test_dict_F)        
    
    def test_flatten_and_expand(self):
        """expand(flatten(d)) == d"""
        res = mapping.expand(mapping.flatten(self.test_dict_F))
        nt.eq_(res, self.test_dict_F)
    
    def test_expand_and_flatten(self):
        """flatten(expand(d)) == d"""
        res = mapping.flatten(mapping.expand(self.test_dict_E))
        nt.eq_(res, self.test_dict_E)

