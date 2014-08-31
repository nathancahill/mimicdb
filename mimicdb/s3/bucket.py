"""MimicDB Bucket subclass wrapper
"""

from boto.s3.bucket import Bucket as BotoBucket
from boto.s3.key import Key as BotoKey

import mimicdb
from .key import Key
from . import tpl


class Bucket(BotoBucket):
    def __init__(self, *args, **kwargs):
        """Set the class for key objects created in the bucket to the MimicDB
        key class.
        """
        kwargs['key_class'] = Key
        super(Bucket, self).__init__(*args, **kwargs)

    def __iter__(self, *args, **kwargs):
        """__iter__ can not be forced to check S3, so return an iterable of
        keys from MimicDB.
        """
        return self.list()

    def get_key(self, *args, **kwargs):
        """Pass 'force' to _get_key_internal() in the headers since the call
        signature of _get_key_internal can not be changed.
        """
        if kwargs.pop('force', None):
            headers = kwargs.get('headers', {})
            headers['force'] = True
            kwargs['headers'] = headers

        super(Bucket, self).get_key(*args, **kwargs)

    def _get_key_internal(self, *args, **kwargs):
        """Return None if key is not in the bucket set.

        Pass 'force' in the headers to check S3 for the key, and after fetching
        the key from S3, save the metadata and key to the bucket set.
        """
        if args[1] is not None and 'force' in args[1]:
            key, res = super(Bucket, self)._get_key_internal(*args, **kwargs)

            if key:
                mimicdb.redis.sadd(tpl.bucket % self.name, key.name)
                mimicdb.redis.hmset(tpl.key % (self.name, key.name),
                                    dict(size=key.size,
                                         md5=key.etag.strip('"')))
            return key, res

        key = None

        if mimicdb.redis.sismember(tpl.bucket % self.name, args[0]):
            key = Key(self)
            key.key = args[0]

        return key, None

    def get_all_keys(self, *args, **kwargs):
        """Pass 'force' in headers to _get_all()
        """
        if kwargs.pop('force', None):
            headers = kwargs.get('headers', args[0] if len(args) else None) or dict()
            headers['force'] = True
            kwargs['headers'] = headers

        return super(Bucket, self).get_all_keys(*args, **kwargs)

    def delete_keys(self, *args, **kwargs):
        """Remove each key or key name in an iterable from the bucket set.
        """
        ikeys = iter(kwargs.get('keys', args[0] if args else []))

        while True:
            try:
                key = ikeys.next()
            except StopIteration:
                break

            if isinstance(key, basestring):
                mimicdb.redis.srem(tpl.bucket % self.name, key)
                mimicdb.redis.delete(tpl.key % (self.name, key))
            elif isinstance(key, BotoKey) or isinstance(key, Key):
                mimicdb.redis.srem(tpl.bucket % self.name, key.name)
                mimicdb.redis.delete(tpl.key % (self.name, key.name))

        return super(Bucket, self).delete_keys(*args, **kwargs)

    def _delete_key_internal(self, *args, **kwargs):
        """Remove key name from bucket set.
        """
        mimicdb.redis.srem(tpl.bucket % self.name, args[0])
        mimicdb.redis.delete(tpl.key % (self.name, args[0]))

        return super(Bucket, self)._delete_key_internal(*args, **kwargs)

    def list(self, *args, **kwargs):
        """Return an iterable of keys from the bucket set. Pass 'force' to
        pull the keys from S3. Force is passed via the headers to _get_all().
        """
        if kwargs.pop('force', None):
            headers = kwargs.get('headers', args[4] if len(args) > 4 else None) or dict()
            headers['force'] = True
            kwargs['headers'] = headers

            for key in super(Bucket, self).list(*args, **kwargs):
                yield key

        else:
            prefix = kwargs.get('prefix', args[0] if args else '')

            for key in mimicdb.redis.smembers(tpl.bucket % self.name):
                if key.startswith(prefix):
                    k = Key(self, key)

                    meta = mimicdb.redis.hgetall(tpl.key % (self.name, key))

                    if meta:
                        k._load_meta(meta['size'], meta['md5'])

                    yield k

    def _get_all(self, *args, **kwargs):
        """If 'force' is in the headers, retrieve the list of keys from S3.
        Otherwise, use the list() function to retrieve the keys from MimicDB.
        """
        headers = kwargs.get('headers', args[2] if len(args) > 2 else None) or dict()

        if 'force' in headers:
            headers.pop('force')

            if len(args) > 2:
                args = list(args)
                args[2] = headers

            return super(Bucket, self)._get_all(*args, **kwargs)

        prefix = kwargs.get('prefix', '')

        return list(self.list(prefix=prefix))

    def sync(self, metadata=False):
        """Sync the bucket set with S3. If metadata=True, a HEAD request is
        performed for each key to download the size and md5 hash of the key.
        """
        for key in mimicdb.redis.smembers(tpl.bucket % self.name):
            mimicdb.redis.delete(tpl.key % (self.name, key))

        mimicdb.redis.delete(tpl.bucket % self.name)
        mimicdb.redis.sadd(tpl.connection, self.name)

        for key in self.list(force=True):
            if metadata:
                self.get_key(key.name, force=True)
            else:
                mimicdb.redis.sadd(tpl.bucket % self.name, key.name)
