.. currentmodule:: pyshell.yaml

:mod:`pyshell.yaml` – Extensions to PyYAML
==========================================

This module is designed to provide a few features to PyYAML_, the YAML parser in python.

- For Python 2.7, enable unicode keys and literals by default in YAML loaders.
- Allow custom mapping types to be used for YAML mappings.
- Allow OrderedDictionaries to be used for dumping and loading, preserving key ordering.

Users can import the custom loaders and dumpers described in :ref:`loaders` and :ref:`dumpers`
to load and dump arbitrary YAML files::

    yaml.load(stream, Loader=MyLoader)
    yaml.dump(data, Dumper=MyDumper)

If you are an end user, and just want a customized loader or dumper, see :ref:`loaders` and :ref:`dumpers`. If you
want to write ordered YAML files in pure unicode, use :class:`PyshellLoader` and :class:`PyshellDumper` respectively.

For developers, there are two interfaces to this module, a class-inheritance based Mixin interface, and a functional
interface. The :ref:`mixin` uses custom class mixins to create new loaders which have the desired behavior.
Using Mixins to create custom loaders and dumpers has the advantage that it does not modify the internal PyYAML
behavior, so other libraries and classes which might use :mod:`yaml` won't be affected by any applied changes.
The :ref:`functions` does modify the behaviors of any :mod:`yaml` laoders and dumpers it acts upon, and
by default, it modifies the :mod:`yaml` included loaders and dumpers. The advantage is that you can modify the
default dumpers and loaders once and then forget about it, the disadvantage is that those changes might propagate
to other modules which use :mod:`yaml`.

.. note:: 
    Since this module changes the parsing and dumping behavior of PyYAML, it is not 
    compatible with the libyaml implementations of the Parser.

.. automodule:: pyshell.yaml

.. _PyYAML: http://pyyaml.org