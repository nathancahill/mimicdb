.. _quickstart:

Quickstart
==========

If you're using Boto already, replace ``boto`` imports with ``mimicdb``
imports.

Change:

.. code-block:: python

    from boto.s3.connection import S3Connection
    from boto.s3.key import Key

To:

.. code-block:: python

    from mimicdb.s3.connection import S3Connection
    from mimicdb.s3.key import Key

Additionally, import the MimicDB object itself, and initiate the
backend:

.. code-block:: python

    from mimicdb import MimicDB
    MimicDB()

After establishing a connection for the first time, sync the connection
to save the metadata locally:

.. code-block:: python

    conn = S3Connection(KEY, SECRET)
    conn.sync()

Or sync only a couple buckets from the connection:

.. code-block:: python

    conn.sync('bucket1', 'bucket2')

After that, upload, download and list as you usually would. API calls
that can be responded to locally will return instantly without hitting
S3 servers. API calls that are made to S3 using MimicDB will be mimicked
locally to ensure consistency with the remote servers.

Pass ``force=True`` to most functions to force a call to the S3 API.
This also updates the local database.
