.. PyShell's SubCommand Tools

.. currentmodule::
    pyshell.subcommand
    
:mod:`subcommand` – Creating commands with Subcommands
======================================================

This module provides scaffolding for subcommand classes. A set of subcommands (:class:`SCEngine`) can be called with the form ``command subcommand --args``. Build each subcommand as a separate class. Connect them all to a controller class using the controller class (:class:`SCController`) list :attr:`SCController.subEngines`.

Writing your own Subcommand
---------------------------

Individual subcommands are defined in a subclass of :class:`SCEngine`. :class:`SCEngine` is a drop-in replacement for :class:`~pyshell.base.CLIEngine`. An existing use of :class:`~pyshell.base.CLIEngine` can be replaced with an inheritance from :class:`SCEngine`. The :class:`SCEngine` instance has all of the same interface methods as :class:`~pyshell.base.CLIEngine`, including :meth:`SCEngine.script` and :meth:`SCEngine.run`. There should be no behavioral difference when an instance of :class:`SCEngine` and an instance of :class:`~pyshell.base.CLIEngine`.

Then add each :class:`SCEngine` class to the :attr:`SCController.subEngines` list on a subclass of :class:`SCController`. :class:`SCController` can be run the same way :class:`~pyshell.base.CLIEngine` works. Both :class:`SCController` and :class:`SCEngine` are subclasses of :class:`~pyshell.base.CLIEngine` and should behave naturally with a :class:`~pyshell.base.CLIEngine`-style configuration.

Running Subcommands
-------------------

How Subcommand Parsing works
----------------------------

Subcommand Execution
--------------------

Configuration and Subcommands
-----------------------------

Command Names
-------------

Base Class API Documentation
----------------------------

.. automodule:: 
    pyshell.subcommand
    
Subcommand Help
---------------

Subcommand Spectial Methods
---------------------------