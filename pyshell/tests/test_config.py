# -*- coding: utf-8 -*-
# 
#  test_config.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-03-30.
#  Copyright 2013 Alexander Rudy. All rights reserved.
# 

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)

import yaml
import pyshell.config as config
from pkg_resources import resource_filename
import nose.tools as nt
import os
from six.moves import cStringIO as StringIO

class test_Configuration(object):
    """pyshell.config.Configuration"""
    
    CLASS = config.Configuration
    
    def setup(self):
        filename = resource_filename(__name__,"test_config/test_config.yml")
        with open(filename,'r') as stream:
            self.test_dict = yaml.load(stream)
        self.test_dict_A = {"Hi":{"A.py.p":1,"B":2,"D":[1,2],"E.py.p":{"F":"G"}},}
        self.test_dict_B = {"Hi":{"A.py.p":3,"C":4,"D":[3,4],"E.py.p":{"F":"G"}},}
        self.test_dict_C = {"Hi":{"A.py.p":3,"B":2,"C":4,"D":[3,4],"E.py.p":{"F":"G"}},} # Should be a merge of A and B
        self.test_dict_D = {"Hi":{"A.py.p":3,"B":2,"C":4,"D":[1,2,3,4],"E.py.p":{"F":"G"}},} # Should be a merge of A and B with a sequence
        self.test_dict_E = {"Hi.A.py.p":3,"Hi.B":2,"Hi.C":4,"Hi.D":[1,2,3,4],"Hi.E.py.p.F":"G"} # Should be a flattening of D
        self.test_dict_F = {"Hi":{"A":{"py":{"p":3}},"B":2,"C":4,"D":[1,2,3,4],"E":{"py":{"p":{"F":"G"}}}},} # Should be an expansion of D

        
    def teardown(self):
        """Remove junky files if they showed up"""
        self.remove("Test.yaml")
        self.remove("Test.dat")
    
    def remove(self,filename):
        """Catch and remove a file whether it exists or not."""
        try:
            os.remove(filename)
        except:
            pass
        
    def test_update(self):
        """.update() deep updates"""
        cfg = self.CLASS(self.test_dict_A)
        cfg.update(self.test_dict_B)
        assert cfg == self.test_dict_C
    
        
    def test_merge(self):
        """.merge() deep updates"""
        cfg = self.CLASS(self.test_dict_A)
        cfg.merge(self.test_dict_B)
        assert cfg == self.test_dict_C
        
    def test_imerge(self):
        """.imerge() deep updates in reverse."""
        cfg = self.CLASS(self.test_dict_B)
        cfg.imerge(self.test_dict_A)
        assert cfg == self.test_dict_C
        
    def test_save(self):
        """.save() writes yaml file or dat file"""
        cfg = self.CLASS(self.test_dict_C)
        cfg.save("Test.yaml")
        loaded = self.CLASS()
        loaded.load("Test.yaml")
        assert self.test_dict_C == loaded.store
        cfg.save("Test.dat")
        
        
    def test_read(self):
        """.load() reads a yaml file."""
        cfg = self.CLASS(self.test_dict_C)
        cfg.save("Test.yaml")
        cfg = self.CLASS()
        cfg.load("Test.yaml")
        assert cfg == self.test_dict_C
        
    def test_read_empty(self):
        """.load() reads an empty yaml file."""
        cfg = self.CLASS()
        cfg.save("Test.yaml")
        cfg = self.CLASS(a="a")
        cfg.load("Test.yaml")
        assert cfg.store == {'a':'a'}
        cfg.load(StringIO(""))
        assert cfg.store == {'a':'a'}
        
class test_DottedConfiguration(test_Configuration):
    """pyshell.config.DottedConfiguration"""
        
    CLASS = config.DottedConfiguration
        
    def test_sub_dictionary(self):
        """Inserting a sub-dictionary"""
        CFG = self.CLASS(**self.test_dict)
        CFG["z"] = self.test_dict_A
        nt.eq_(CFG["z.Hi.B"], CFG.store["z"]["Hi"]["B"])
        
    def test_sub_dotted_dictionary(self):
        """Inerting a dotted sub-dictionary"""
        CFG = self.CLASS(**self.test_dict)
        CFG["z"] = {'a.b':'c'}
        nt.eq_(CFG["z.a.b"], CFG.store["z"]["a.b"])
        
    def test_multiple_sub_dotted_dictionaries(self):
        """Lookup with multiple correct paths."""
        CFG = self.CLASS(**self.test_dict)
        CFG["z"] = {'a.b':'c','a':{'b':'d'}}
        nt.eq_(CFG["z.a.b"],'c')
        nt.eq_(CFG["z.a"]["b"],'d')
        
    def test_sub_dotted_contains(self):
        """Testing contains for dotted names."""
        CFG = self.CLASS(**self.test_dict)
        CFG["z"] = {'a.b':'c'}
        nt.ok_("a.b" in CFG["z"], "Couldn't find 'a.b' in {:s}".format(CFG["z"]))
        nt.ok_("a" not in CFG["z"], "Found 'a' in {:s}".format(CFG["z"]))
        nt.ok_("d" not in CFG["z"], "Found 'd' in {:s}".format(CFG["z"]))
        
    def test_sub_dotted_del(self):
        """Testing contains for dotted names."""
        CFG = self.CLASS(**self.test_dict)
        CFG["z"] = {'a.b':'c'}
        del CFG["z.a.b"]
        nt.ok_("a.b" not in CFG["z"], "Found 'a.b' (not deleted) in {:s}".format(CFG["z"]))
        del CFG["c.d"]
        nt.ok_("c.d" not in CFG, "Found 'c.d' (not deleted) in {:s}".format(CFG))
        
    @nt.raises(KeyError)
    def test_sub_dotted_dictionary_fail(self):
        """Inerting a dotted sub-dictionary, KeyError"""
        CFG = self.CLASS(**self.test_dict)
        CFG["z"] = {'a.b':'c'}
        CFG["z.a"]
        
    def test_get_dotted_name(self):
        """Get keys with periods in them."""
        CFG = self.CLASS(**self.test_dict)
        nt.eq_(CFG["g.h.i.j.k"], CFG["g"]["h.i.j"]["k"])
        nt.eq_(CFG["g.h.i.j.k"], CFG.store["g"]["h.i.j"]["k"])
        
    def test_get_empty_name(self):
        """Get values which are empty"""
        CFG = self.CLASS(**self.test_dict)
        nt.eq_(CFG["c.f"], {})
        
    @nt.raises(KeyError)
    def test_get_bad_name(self):
        """KeyError values which don't exist."""
        CFG = self.CLASS(**self.test_dict)
        CFG["g.h"]
        
    @nt.raises(KeyError)
    def test_get_bad_ml_name(self):
        """KeyError values which don't exist many levels deep"""
        CFG = self.CLASS(**self.test_dict)
        CFG.get("z.a.b","h")
        CFG["z.a.b"]
    
    def test_set_dotted_name(self):
        """Set for keys with periods in them"""
        CFG = self.CLASS(**self.test_dict)
        CFG["g.h"] = 'a'
        nt.eq_(CFG["g.h"],'a')
        nt.eq_(CFG["g"]["h"],'a')
        
    def test_set_deep_dotted_name(self):
        """Set for keys with many periods in them."""
        CFG = self.CLASS(**self.test_dict)
        CFG["g.h.z.f.k"] = 'a'
        nt.eq_(CFG["g.h.z.f.k"],'a')
        nt.eq_(CFG["g"]["h.z.f.k"],'a')
        
    def test_get_deep_class(self):
        """Deep class transfer."""
        CFG = self.CLASS()
        CFG.merge(self.test_dict)
        assert isinstance(CFG["c.l"],CFG.dn)
        
    def test_separator_change(self):
        """Change separator"""
        CFG = self.CLASS()
        CFG.separator = "-"
        CFG["A-B-C"] = 2
        nt.eq_(CFG["A"]["B"]["C"],2)
        CFG.merge({'A':{'B':{'D':3}}})
        nt.eq_(CFG["A-B-D"],3)
        del CFG["A-B-C"]
        nt.ok_("A-B-C" not in CFG)
        
        
class test_StructuredConfiguration(test_DottedConfiguration):
    """pyshell.config.StructuredConfiguration"""
    
    CLASS = config.StructuredConfiguration
        