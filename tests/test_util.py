# 
#  test_util.py
#  pyshell
#  
#  Created by Jaberwocky on 2013-04-01.
#  Copyright 2013 Jaberwocky. All rights reserved.
# 
"""pyshell.util"""

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)


import pyshell.util
import nose.tools as nt

def test_ipydb():
    """Test activation of the iPython debugger."""
    import sys, os.path
    original_file = sys.modules['__main__'].__file__
    pyshell.util.ipydb()
    nt.eq_(sys.modules['__main__'].__file__,original_file)
    
    
def test_is_type_factory():
    """is_type_factory(type)"""
    is_int = pyshell.util.is_type_factory(int)
    nt.eq_( is_int.__doc__, "Checks if obj can be *cast* as <type 'int'>.")
    nt.eq_( is_int.__hlp__, "Input must be an <type 'int'>")
    nt.ok_(is_int("1"),"The string '1' should be a valid integer literal")
    nt.ok_(is_int("244920"),"The string '244920' should be a valid integer literal")
    nt.ok_(not is_int("1.1"),"The string '1.1' should not be a valid integer literal")
    nt.ok_(not is_int("Bogus"),"The string 'Bogus' should not be a valid integer literal")
    
def test_force_dir_path():
    """force_dir_path(path)"""
    PATHS = [
        ('/some//path/here','/some/path/here/'),
        ('/some//path/here//','/some/path/here/'),
        ('another/path/here','another/path/here/'),
        ('filename.txt','filename.txt/'),
        ('valid/path/','valid/path/')
    ]
    for qpath, apath in PATHS:
        nt.eq_(apath,pyshell.util.force_dir_path(qpath))
        
def test_collapseuser():
    """collapseuser(path)"""
    import os.path
    PATHS = [
        (os.path.expanduser("~"),"~"),
        (os.path.join(os.path.expanduser("~"),"another","path","part"),'~/another/path/part'),
        (os.path.expanduser("~")+"//another/path/part",'~/another/path/part'),
        ('/another/path/here','/another/path/here'),
        ('valid/path/','valid/path/')
    ]
    for qpath, apath in PATHS:
        nt.eq_(apath,pyshell.util.collapseuser(qpath))
        
def test_is_remote_path():
    """is_remote_path(path)"""
    PATHS = [
        ('user@host:port:home/somewhere',True),
        ('host:home/somewhere',True),
        ('host:/root/somewhere',True),
        ('/another/path/here',False),
        ('valid/path/',False)
    ]
    for qpath, apath in PATHS:
        nt.eq_(apath,pyshell.util.is_remote_path(qpath))
    
@nt.raises(NotImplementedError)
def test_semiabstractmethod_decorator():
    """@semiabstractmethod"""
    @pyshell.util.semiabstractmethod
    def my_method():
        """test-doc"""
        print "Doing my not-implemented method"
    
    nt.eq_(my_method.__name__,'my_method')
    nt.eq_(my_method.__doc__,'test-doc')
    my_method()
    
@nt.raises(NotImplementedError)
def test_semiabstractmethod_decorator_with_args():
    """@semiabstractmethod(message)"""
    @pyshell.util.semiabstractmethod("My Message %s()")
    def my_method():
        """test-doc"""
        print "Doing my not-implemented method"

    nt.eq_(my_method.__name__,'my_method')
    nt.eq_(my_method.__doc__,'test-doc')
    my_method()
    