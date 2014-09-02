.. _forcing:

********************
Forcing S3 API Calls
********************

All of Boto's S3 classes and functions are wrapped in MimicDB functions to
provide access to the local data instead of the S3 API. This means that
changes to buckets and keys on S3 (outside of MimicDB), won't be
reflected in MimicDB unless the API call is forced.

Forcing an S3 API call also stores the response in MimicDB, so the forced call
only has to happen once to retrieve new changes.

In most cases, passing ``force=True`` to the function will cause the S3 API call
to be executed.

.. warning::

    ``Bucket.__iter__`` can not have arguments passed to it, so it defaults to
    not calling the API.


The following functions can be forced:

.. automethod:: mimicdb.s3.connection.S3Connection.get_bucket

.. automethod:: mimicdb.s3.connection.S3Connection.get_all_buckets

.. automethod:: mimicdb.s3.bucket.Bucket.get_key

.. automethod:: mimicdb.s3.bucket.Bucket.get_all_keys

.. automethod:: mimicdb.s3.bucket.Bucket.list
