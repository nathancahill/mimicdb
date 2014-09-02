"""MimicDB S3Connection subclass wrapper
"""

from boto.s3.connection import S3Connection as BotoS3Connection
from boto.exception import S3ResponseError

import mimicdb
from .bucket import Bucket
from ..backends import tpl


class S3Connection(BotoS3Connection):
    def __init__(self, *args, **kwargs):
        """Set the base class for bucket objects created in the connection to
        the MimicDB bucket class.
        """
        kwargs['bucket_class'] = Bucket
        super(S3Connection, self).__init__(*args, **kwargs)

    def get_all_buckets(self, *args, **kwargs):
        """Return a list of buckets in MimicDB.

        :param boolean force: If true, API call is forced to S3
        """
        if kwargs.pop('force', None):
            buckets = super(S3Connection, self).get_all_buckets(*args, **kwargs)

            for bucket in buckets:
                mimicdb.backend.sadd(tpl.connection, bucket.name)

            return buckets

        return [Bucket(self, bucket) for bucket in mimicdb.backend.smembers(tpl.connection)]

    def get_bucket(self, bucket_name, validate=True, headers=None, force=None):
        """Return a bucket from MimicDB if it exists. Return a
        S3ResponseError if the bucket does not exist and validate is passed.

        :param boolean force: If true, API call is forced to S3
        """
        if force:
            bucket = super(S3Connection, self).get_bucket(bucket_name, validate, headers)
            mimicdb.backend.sadd(tpl.connection, bucket.name)
            return bucket

        if mimicdb.backend.sismember(tpl.connection, bucket_name):
            return Bucket(self, bucket_name)
        else:
            if validate:
                raise S3ResponseError(404, 'NoSuchBucket')
            else:
                return Bucket(self, bucket_name)

    def create_bucket(self, *args, **kwargs):
        """Add the bucket to MimicDB after successful creation.
        """
        bucket = super(S3Connection, self).create_bucket(*args, **kwargs)

        if bucket:
            mimicdb.backend.sadd(tpl.connection, bucket.name)

        return bucket

    def delete_bucket(self, *args, **kwargs):
        """Delete the bucket on S3 before removing it from MimicDB.
        If the delete fails (usually because the bucket is not empty), do
        not remove the bucket from the set.
        """
        super(S3Connection, self).delete_bucket(*args, **kwargs)

        bucket = kwargs.get('bucket_name', args[0] if args else None)

        if bucket:
            mimicdb.backend.srem(tpl.connection, bucket)

    def sync(self, *buckets):
        """Sync either a list of buckets or the entire connection.

        Force all API calls to S3 and populate the database with the current
        state of S3.

        :param \*string \*buckets: Buckets to sync
        """
        if buckets:
            for _bucket in buckets:
                for key in mimicdb.backend.smembers(tpl.bucket % _bucket):
                    mimicdb.backend.delete(tpl.key % (_bucket, key))

                mimicdb.backend.delete(tpl.bucket % _bucket)

                bucket = self.get_bucket(_bucket, force=True)

                for key in bucket.list(force=True):
                    mimicdb.backend.sadd(tpl.bucket % bucket, key.name)
                    mimicdb.backend.hmset(tpl.key % (bucket, key.name), dict(size=key.size, md5=key.etag.strip('"')))
        else:
            for bucket in mimicdb.backend.smembers(tpl.connection):
                for key in mimicdb.backend.smembers(tpl.bucket % bucket):
                    mimicdb.backend.delete(tpl.key % (bucket, key))

                mimicdb.backend.delete(tpl.bucket % bucket)

            for bucket in self.get_all_buckets(force=True):
                for key in bucket.list(force=True):
                    mimicdb.backend.sadd(tpl.bucket % bucket.name, key.name)
                    mimicdb.backend.hmset(tpl.key % (bucket.name, key.name), dict(size=key.size, md5=key.etag.strip('"')))
