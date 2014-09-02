.. _syncing:

****************
Syncing S3 State
****************

If there are buckets or keys on S3 before starting to use MimicDB, it's
important to sync the connection to ensure consistency with the S3 API in
future calls.

Syncing only has to be run once. Be aware that buckets with large numbers of
keys can take a long time to sync. It's best to not use S3Connection.sync()
in frequently used code paths.

All MimicDB data in the synced buckets is cleared before syncing to ensure a
clean slate.

.. code-block:: python

    from mimicdb.s3.connection import S3Connection

    conn = S3Connection(KEY, SECRET)
    conn.sync()

.. automethod:: mimicdb.s3.connection.S3Connection.sync

.. automethod:: mimicdb.s3.bucket.Bucket.sync
