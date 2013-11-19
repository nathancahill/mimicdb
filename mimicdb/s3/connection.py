from boto.s3.connection import S3Connection as boto_S3Connection
from boto.exception import S3ResponseError

import mimicdb
from mimicdb.s3.bucket import Bucket


class S3Connection(boto_S3Connection):
    def __init__(self, *args, **kwargs):
        """
        Sets the base class for bucket objects created in the connection to the
        MimicDB class.
        """
        kwargs['bucket_class'] = Bucket
        super(S3Connection, self).__init__(*args, **kwargs)


    def get_all_buckets(self, *args, **kwargs):
        """
        Retrieve buckets from the 'mimicdb' set. Passing 'force' checks S3 for
        the list of buckets.
        """
        if kwargs.pop('force', None):
            buckets = super(S3Connection, self).get_all_buckets(*args, **kwargs)

            for bucket in buckets:
                mimicdb.redis.sadd('mimicdb', bucket.name)

            return buckets

        return [Bucket(self, bucket) for bucket in mimicdb.redis.smembers('mimicdb')]


    def get_bucket(self, *args, **kwargs):
        """
        Retrieves a bucket from the 'mimicdb' set if it exists. Simulates an
        S3ResponseError if the bucket does not exist (and validate is passed).
        """
        if kwargs.pop('force', None):
            bucket = super(S3Connection, self).get_bucket(*args, **kwargs)

            mimicdb.redis.sadd('mimicdb', bucket.name)

            return bucket

        name = kwargs.get('bucket_name', args[0] if args else None)
        validate = kwargs.get('validate', args[0] if args else True)

        if not name:
            raise ValueError

        if mimicdb.redis.sismember('mimicdb', name):
            return Bucket(name)
        else:
            if validate:
                raise S3ResponseError(404, 'NoSuchBucket')


    def create_bucket(self, *args, **kwargs):
        """
        Add the bucket name to the mimicdb set.
        """
        bucket = kwargs.get('bucket_name', args[0] if args else None)

        if bucket:
            mimicdb.redis.sadd('mimicdb', bucket)

        return super(S3Connection, self).create_bucket(*args, **kwargs)


    def delete_bucket(self, *args, **kwargs):
        """
        Deletes the bucket on S3 before removing it from the mimicdb set.
        If the delete fails (usually because the bucket is not empty), it does
        not remove the bucket from the set.
        """
        super(S3Connection, self).delete_bucket(*args, **kwargs)

        bucket = kwargs.get('bucket_name', args[0] if args else None)

        if bucket:
            mimicdb.redis.srem('mimicdb', bucket)


    def sync(self, bucket=None):
        """
        Syncs either a bucket or the entire connection.

        Bucket names are stored in a set named 'mimicdb'.
        Key names are stored in a set with the same name as the bucket.

        Key metadata is in the format 'bucket:key:size'.

        Syncing overrides the MimicDB functionality and forces API calls to S3.

        Calling sync() populates the database with the current state of S3.
        When syncing the entire connection, the mimicdb set and all bucket sets
        are wiped before being re-populated. When syncing a bucket, the bucket set
        is wiped before it is re-populated.
        """
        if bucket:
            bucket = self.get_bucket(bucket)

            mimicdb.redis.sadd('mimicdb', bucket.name)

            for key in mimicdb.redis.smembers(bucket.name):
                mimicdb.redis.delete('%(bucket)s:%(key)s:size' % dict(bucket=bucket, key=key))

            mimicdb.redis.delete(bucket.name)

            for key in bucket.list(force=True):
                mimicdb.redis.sadd(bucket.name, key.name)
                mimicdb.redis.set((key.base + ':size') % dict(bucket=bucket.name, key=key.name), key.size)

        else:
            for bucket in mimicdb.redis.smembers('mimicdb'):
                for key in mimicdb.redis.smembers(bucket):
                    mimicdb.redis.delete('%(bucket)s:%(key)s:size' % dict(bucket=bucket, key=key))

                mimicdb.redis.delete(bucket)

            mimicdb.redis.delete('mimicdb')

            buckets = self.get_all_buckets(force=True)

            for bucket in buckets:
                mimicdb.redis.sadd('mimicdb', bucket.name)

                for key in bucket.list(force=True):
                    mimicdb.redis.sadd(bucket.name, key.name)
                    mimicdb.redis.set((key.base + ':size') % dict(bucket=bucket.name, key=key.name), key.size)
