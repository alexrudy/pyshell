Overview
========

:mod:`pyshell` is a object-oriented framework for command line tools in Python. It provides a conveninet way to build up command line interfaces and tools using object inheritance. :mod:`pyshell` also contains a YAML-based configuration tool, for storing, accessing and using hierarchical configuration files.

Installation
------------

To install :mod:`pyshell`, I recommend using the ``pip`` command::
    
    pip install https://github.com/alexrudy/pyshell/archive/0.4.1.zip
    

.. note:: As a single developer, I don't always get around to releasing the absolute latest additions and changes to my work. If you want the bleeding edge latest work, I suggest you use the copy on GitHub: https://github.com/alexrudy/pyshell/ . It can be installed like this::
        
        git clone https://github.com/alexrudy/pyshell.git
        cd pyshell
        python setup.py install
        
    I'd appreciate news of any bugs you find in the development version. You can leave an issue on GitHub at https://github.com/alexrudy/pyshell/issues .
    
Philosophy
----------

The command line interface tools which this package can build are designed to be object inheritance based tools. To use them properly, you'll have to subclass them. Sometimes this can be done simply. Subclasses of the :class:`~pyshell.CLIEngine` need only define a :meth:`~pyshell.CLIEngine.do` method to operate correctly.