Configuration: YAML based nested dictionaries
=============================================

This module provides nested dictionaries which can be serialized as YAML files. The dictionaries can be created like any usual dictionary, so long as they are constructed from the class. Elements of either a :class:`StructuredConfiguration` or :class:`DottedConfiguration` can be accessed using a special "."-separated key syntax. The dictionary is nested, so you can do the following::

    >>> MyConfig = DottedConfiguration({"a":{"b":{"c":1}}})
    >>> MyConfig["a"]["b"]["c"]
    1
    >>> MyConfig["a.b.c"]
    1


.. automodule:: pyshell.config

    Developer Notes
    ---------------

    There are a few design decisions in :mod:`pyshell.config` that are worth explaining.

    The configuration items work with an internal storage object. That storage object is a dictionary of dictionaries, in its purest form. Configuration classes are responsible for re-casting any returned value as the correct external configuration object when accessed. This should be done as lightly as possible (i.e. only on the first layer, not renested).

    There is some tricky handling of dictionary keys which contain the default separator, ``"."``. The following rules apply:

    - Dictionaries inserted with dotted keys remain intact.
    - Dotted keys inserted are interperted as heirarchical keys.
    - Heirarchical keys will be retrieved only when the key can't be interpreted as a dotted key.
    - To retrieve a heirarchical key which is `hidden` by a dotted key, retrieve the key levels as separate items, without the ``"."``


    When writing to YAML files, there are two callback functions which can be used to encapsulate metadata, or multiple YAML documents in a single document. By default, the included YAML reader reads documents separated by ``---``. Only the last document is the configuration interpreted by the :class:`~pyshell.config.Configuration` object. The other documents are passed to :meth:`~pyshell.config.Configuration._load_yaml_callback`, which accepts many arguments as individual YAML documents. To save multiple YAML documents as output, the extra YAML documents should be returned as a list by :meth:`~pyshell.config.Configuration._save_yaml_callback`. If you don't want to save any extra documents, :meth:`~pyshell.config.Configuration._save_yaml_callback` may return an empty list (as it does by default). These callback functions could be used to silently change the underlying configuration object before serialization to YAML. This behavior has not been tested.


