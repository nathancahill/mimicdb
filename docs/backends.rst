.. _backends:

********
Backends
********

Besides the default Redis backend, MimicDB has SQLite and in-memory
backends available. To use a different backend, pass an instance of it to the
MimicDB ``__init__`` function:

.. code-block:: python

    from mimicdb import MimicDB
    from mimicdb.backends.sqlite import SQLite

    MimicDB(backend=SQLite())


Keep in mind that the default database for the SQLite backend is an in-memory
database. It, along with the in-memory backend, will be destroyed when the
process finishes running. For persistent data, use Redis or a custom backend.

.. automodule:: mimicdb.backends
    :members:

.. automodule:: mimicdb.backends.default
    :members:

.. automodule:: mimicdb.backends.sqlite
    :members:

.. automodule:: mimicdb.backends.memory
    :members:
