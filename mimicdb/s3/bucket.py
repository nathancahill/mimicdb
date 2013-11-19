from boto.s3.bucket import Bucket as boto_Bucket
from boto.s3.key import Key as boto_Key

import mimicdb
from mimicdb.s3.key import Key


class Bucket(boto_Bucket):
    def __init__(self, *args, **kwargs):
        """
        Sets the base class for key objects created in the bucket to the MimicDB
        class.
        """
        kwargs['key_class'] = Key
        super(Bucket, self).__init__(*args, **kwargs)

    def __iter__(self, *args, **kwargs):
        """
        __iter__ can not be forced to check S3, so it returns an iterable of
        keys from MimicDB.
        """
        return self.list()

    def get_key(self, *args, **kwargs):
        """
        Checks if a key exists in the bucket set. Returns None if not. Uses
        the headers hack to pass 'force' to internal method: _get_key_internal()
        """
        if kwargs.pop('force', None):
            headers = kwargs.get('headers', {})
            headers['force'] = 'True'
            kwargs['headers'] = headers

        return super(Bucket, self).get_key(*args, **kwargs)

    def _get_key_internal(self, *args, **kwargs):
        """
        Internal method for checking if a key exists in the bucket set. Returns
        None if not. If 'force' is in the headers, it checks S3 for the key.
        """
        if 'force' in kwargs.get('headers', args[1] if len(args) > 1 else {}) or kwargs.pop('force', None):
            return super(Bucket, self)._get_key_internal(*args, **kwargs)

        key = None

        if mimicdb.redis.sismember(self.name, args[0]):
            key = Key(self)

        return key, None

    def delete_keys(self, *args, **kwargs):
        """
        Remove each key or key name in an iterable from the bucket set.
        """
        ikeys = iter(kwargs.get('keys', args[0] if args else []))

        while True:
            try:
                key = ikeys.next()
            except StopIteration:
                break

            if isinstance(key, basestring):
                mimicdb.redis.srem(self.name, key)
            elif isinstance(key, boto_Key) or isinstance(key, Key):
                mimicdb.redis.srem(self.name, key.name)

        return super(Bucket, self).delete_keys(*args, **kwargs)

    def _delete_key_internal(self, *args, **kwargs):
        """
        Remove key name from bucket set before deleting it.
        """
        key = kwargs.get('key_name', args[0] if args else None)

        if key:
            mimicdb.redis.srem(self.name, key)

        return super(Bucket, self)._delete_key_internal(*args, **kwargs)

    def list(self, *args, **kwargs):
        """
        Returns an iterable of keys in the bucket set. If 'force' is passed,
        it passes it to the internal function using the headers hack.

        """
        if kwargs.pop('force', None):
            headers = kwargs.get('headers', {})
            headers['force'] = 'True'
            kwargs['headers'] = headers

            for key in super(Bucket, self).list(*args, **kwargs):
                yield key

        else:
            prefix = kwargs.get('prefix', args[0] if args else '')

            for key in mimicdb.redis.smembers(self.name):
                if key.startswith(prefix):
                    yield Key(self, key)

    def _get_all(self, *args, **kwargs):
        """
        Internal method for listing keys in a bucket set. If 'force' is in the
        headers, it retrieves the list of keys from S3.

        """
        if 'force' in kwargs.get('headers', args[2] if len(args) > 2 else {}) or kwargs.pop('force', None):
            headers = kwargs.get('headers', {})

            if headers == dict():
                kwargs.pop('headers', None)
            else:
                kwargs['headers'] = headers

            return super(Bucket, self)._get_all(*args, **kwargs)

        prefix = kwargs.get('prefix', '')

        return list(self.list(prefix=prefix))


    def sync(self):
        """
        Syncs the bucket with S3. The bucket set is wiped before being re-populated.
        """
        mimicdb.redis.sadd('mimicdb', self.name)

        for key in mimicdb.redis.smembers(self.name):
            mimicdb.redis.delete('%(bucket)s:%(key)s:size' % dict(bucket=self.name, key=key))

        mimicdb.redis.delete(self.name)

        for key in self.list(force=True):
            mimicdb.redis.sadd(self.name, key.name)
            mimicdb.redis.set((key.base + ':size') % dict(bucket=self.name, key=key.name), key.size)
