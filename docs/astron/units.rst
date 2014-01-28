Tools for using Units
=====================

This module contains descriptors for using units. Descriptors
are objects that behave like properties. The python documentaion on
|descriptors| provides a good introduction. To use a descriptor::
    
    >>> class MyObject(object):
    ...    
    ...    height = UnitsProperty('height', u.m)
    ...    
    ...
    >>> MyInstance = MyObject()
    >>> MyInstance.height = 10
    >>> MyInstance.height
    10 m


.. automodule:: pyshell.astron.units
    :members:


.. |descriptors| replace:: `descriptors`_

.. _descriptors: http://docs.python.org/2/howto/descriptor.html