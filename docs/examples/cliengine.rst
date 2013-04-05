.. _cliengine_examples:

:class:`CLIEngine` Examples
===========================

The simplest example we can possibly think of is below. All it does is print a line to the command line when run, but it uses the power of :class:`CLIEngine` to make a basic command line script.

.. literalinclude:: ../../examples/basic.py

Using command line arguments only requires a little bit more work. The example below shows many of the possible things that you can do using a simple configuration file and command line arguments:

.. literalinclude:: ../../examples/hello.py

The configuration file used by this script is:

.. literalinclude:: ../../examples/hello.yml