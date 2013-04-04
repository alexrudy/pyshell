# 
#  test_config.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-03-30.
#  Copyright 2013 Alexander Rudy. All rights reserved.
# 

import yaml
import pyshell.config as config
from pkg_resources import resource_filename
import nose.tools as nt
import os

class test_Configuration(object):
    """pyshell.config.Configuration"""
    
    CLASS = config.Configuration
    
    def setup(self):
        filename = resource_filename(__name__,"test_config/test_config.yml")
        with open(filename,'r') as stream:
            self.test_dict = yaml.load(stream)
        self.test_dict_A = {"Hi":{"A":1,"B":2,},}
        self.test_dict_B = {"Hi":{"A":3,"C":4,},}
        self.test_dict_C = {"Hi":{"A":3,"B":2,"C":4,},} #Should be a merge of A and B
        
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
        
    def test_save(self):
        """.save() writes yaml file or dat file"""
        cfg = self.CLASS(self.test_dict_C)
        cfg.save("Test.yaml")
        loaded = self.CLASS()
        loaded.load("Test.yaml")
        assert self.test_dict_C == loaded.extract()
        cfg.save("Test.dat")
        
        
    def test_read(self):
        """.load() reads a yaml file."""
        cfg = self.CLASS(self.test_dict_C)
        cfg.save("Test.yaml")
        cfg = self.CLASS()
        cfg.load("Test.yaml")
        assert cfg == self.test_dict_C
        
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
        
    @nt.raises(KeyError)
    def test_sub_dotted_dictionary(self):
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
        
    
    def test_set_dotted_name(self):
        """Set for keys with periods in them"""
        CFG = self.CLASS(**self.test_dict)
        CFG["g.h"] = 'a'
        nt.eq_(CFG["g.h"],'a')
        CFG["g"]
        
class test_StructuredConfiguration(test_DottedConfiguration):
    """pyshell.config.StructuredConfiguration"""
    
    CLASS = config.StructuredConfiguration
        