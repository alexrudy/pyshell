.. currentmodule: pyshell.base

:class:`CLIEngine` – a base for Command Line Interfaces
=======================================================

The :class:`CLIEngine` is designed with "Convention over Configuration"
in mind. That is, it aims to set everything up so that it will work out-of-the-box, 
and the user is responsbile for adjusting undesireable
behavior. Basically, all you have to do is write a subclass of
:class:`CLIEngine` with only a :meth:`~CLIEngine.do` method (no need for
:meth:`__init__`!). See :ref:`cliengine_examples` for examples.

Writing your own Engine
-----------------------
    
This class should be subclassed by the user, who should re-implement 
the following methods:
    
- :meth:`~CLIEngine.do`  - Does the 'real work'.
- :meth:`~CLIEngine.kill` - Called if the engine tries to exit abnormally.
    
These funcitons are used in the normal operation of the command line engine.
    
The user should also override the desired instance variables on the class.
Useful instance variables to consider overriding are 
:attr:`~CLIEngine.defaultcfg` and :attr:`~CLIEngine.description`

There are some methods that the user can optionally override to alter the
behavior of the :class:`CLIEngine` on startup. These are:

- :meth:`~CLIEngine.init` should add arguments to the :attr:`parser`
  which are fully formed **before** configuration.
- :meth:`~CLIEngine.before_configure` should perform actions on the 
  configuration which will be **overwritten** by any configuration file 
  values.
- :meth:`~CLIEngine.after_configure` should perform actions on the 
  configuration which must occur before command line arguments are parsed
  by :meth:`~CLIEngine.parse`


Other methods are used to control the engine during normal operation. These 
methods should in general not be overwritten, but can be modified in 
subclasses, so long as they are called using the 
``super(ClassName, self).method()`` construct.
    
Running your Engine
-------------------

To run the engine, use :meth:`~CLIEngine.run`. To run the engine without 
instantiating the class, use :meth:`~CLIEngine.script`, a class method 
that instantiates a new object, and runs the tool. Both methods 
accomplish the same thing at the end of the day.

Using ``__main__`` or just running the file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To run your command as a simple python file, write your command class, then 
call :meth:`~CLIEngine.script`. You can use :meth:`~CLIEngine.script` to 
start the engine with the "if main" python convention::

    if __name__ == '__main__':
        Engine.script()

You can also call :meth:`~CLIEngine.script` outside of an "if main" block.
Be aware, however, that :meth:`~CLIEngine.script` will use the command line
arguments passed to the python interpreter as a whole!

Using :mod:`distutils`
~~~~~~~~~~~~~~~~~~~~~~

Using :meth:`~CLIEngine.script` allows the developer to set this as
an entry point in their ``setup.py`` file, and so provide the command
line enegine as a command line tool in a distutils supported python package.
A basic entry point for this tool would appear in the ``console_scripts`` key 
like ::
    
    [ "PyScript = mymodule.cli:Engine.script" ]
    

These console scripts can be installed using ``python setup.py install``. A 
helper will be placed in your python script path (watch the ``setup.py`` output
to see where that is!). The helper script manages the call to your class.

Running without a command-line
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want run the :class:`CLIEngine` without gobbling the command line arguments
passed to python, you'll have to instantiate the :class:`CLIEngine` object yourself.
By default, the :class:`CLIEngine` constructor takes no arguments. You should pass
any pseudo-command-line-arguments to :meth:`~CLIEngine.arguments`. Each arguemnt item
should be a separate iterable member, so ``"--config somefile.yml"`` should be passed 
in as ``["--config","somefile.yml"]``. A minimal :class:`CLIEngine` call would look like::

    ENG = CLIEngine()
    ENG.arguments('-foo','bar')
    ENG.run()

.. Note::
    To parse no command line arguments, pass something in like ``tuple()`` to act as the empty set of arguments.

How :class:`CLIEngine` works
----------------------------

The engine is set up to use a configuration file system, 
provide basic parsing attributes, and an interruptable 
command line interaction flow. The configuration is designed 
to provide dynamic output and to configure the system 
before it completes the parsing process.

1.  Initialization sets up the object, and sets up the argument parser.
    Method :meth:`~CLIEngine.init` is called at this point.
    The parser should only understand arguments that will not
    be impacted by any configuration values. At this stage, by default, the
    parser is aware of the ``--config`` argument. This allows the
    :class:`CLIEngine` to load a user-specified configuration file, and to
    use that configuration file to affect the command line arguments presented
    and parsed.

2.  Preliminary Arguments are parsed by :meth:`~CLIEngine.arguments`.

3.  Configuration is handled by the :meth:`~CLIEngine.configure` function. This 
    function loads the following configuration files in order (such that the 
    last one loaded is the one that takes precedence):

    *   The ``defaultcfg`` file from ``engine.__module__``. This allows the 
        developer to provide a base configuration for the engine.

    *   The requested configuration file from the user's home directory.

    *   The requested configuration file form the current directory.

    *   If no configuration file is requested, the filename for `defaultcfg` 
        will be used. As well, if the engine cannot find the requested 
        configureation file in the current directory (i.e. the user asks for 
        a file, and it isn't there) a warning will be issued.

4.  Help message is inserted into parsing, and remaining arguments
    parsed by :meth:`~CLIEngine.parse`. At this point, the entire configuration process
    is complete.

5.  The function :meth:`~CLIEngine.do` is called, This should do the bulk of the engine's
    work.

6.  If the user interrupts the operation of the program, :meth:`~CLIEngine.kill` will
    be called. If python is in ``__debug__`` mode, this will raise a full
    traceback. If not, the traceback will be suppressed.

Configuration
-------------

:class:`CLIEngine` uses :class:`~pyshell.config.StructuredConfiguration` 
objects. These objects represent rich nested mapping types with fast 
accessors and quick access to configuration file services using :mod:`PyYAML`.

To entirely disable configuration, and remove the configuration object, set 
:attr:`CLIEngine.defaultcfg` to ``False``. This will prevent the 
:class:`CLIEngine` from adding the ``--config`` and ``--configure`` command 
line options, and will not load any data from YAML files.

Configuration is a powerful, heirarchical system. To understand the load 
order, see :meth:`pyshell.config.StructuredConfiguration.configure`. 
However, there are several levels where you can customize the order of 
loaded configurations. Configurations loaded earlier in the system will 
be overwritten by those loaded later.

* :attr:`CLIEngine.supercfg` allows the developer to set confguration 
  files which should be loaded before all others.
* :attr:`CLIEngine.defaultcfg` allows the developer to set **both** the 
  configuration file name which should be loaded from the 
  ``CLIEngine``-subclass's directory (think ``os.path.dirname(__file__)``),
  and the configuration file which will be searched for in the current 
  directory.
* ``--config`` can change the name of the configuration file to look
  for in the current directory.
* ``--configure`` can write new configuration values into the configuration
  at the end of the configuration loading process.

Command Line Help
-----------------

Command Line Help is triggered when it parses the ``-h`` argument. When
calling :meth:`~CLIEngine.script`, the help text will be printed to the
terminal.

Command line arguments and help in :class:`CLIEngine` are handled by an
internal :class:`argparse.ArgumentParser` instance. The documentation for
:mod:`argparse` in the python core provides instructions for using a parser.

The parser set up in :class:`CLIEngine` uses the class attribute
:attr:`CLIEngine.description` to set a help description. The attribute
:attr:`CLIEngine.epilog` sets the parser epilog in text. 

Reference for :class:`CLIEngine`, the Command Line Interface Engine
-------------------------------------------------------------------

.. automodule::
    pyshell.base
    :members:

Call structure of :meth:`run`
-----------------------------
The call structure of the method :meth:`~CLIEngine.run`, the main script driver.
This is provided as a reference. Note that the :meth:`~CLIEngine.init` is called
during :meth:`~CLIEngine.arguments` when :meth:`~CLIEngine.arguments` is called
outside of :meth:`~CLIEngine.run`, allowing you to use the following sequence to
run a subclass of :class:`CLIEngine`::
    
    CLIInstance = CLIEngine()
    CLIInstance.arguments("--faked CLI --arguments".split())
    CLIInstance.run()
    

.. literalinclude:: ../pyshell/base.py
    :linenos:
    :pyobject: CLIEngine.run

