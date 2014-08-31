import os
import hashlib
import logging
import unittest

import redis

from boto.s3.connection import S3Connection as BotoS3Connection
from boto.s3.bucket import Bucket as BotoBucket
from boto.s3.key import Key as BotoKey
from boto.exception import S3CreateError, S3ResponseError

import mimicdb
from mimicdb import MimicDB
from mimicdb.s3.connection import S3Connection
from mimicdb.s3.bucket import Bucket
from mimicdb.s3.key import Key
from mimicdb.s3 import tpl

AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

logging.getLogger('boto').setLevel(logging.CRITICAL)

class MimicDBTestCase(unittest.TestCase):
    def setUp(self):
        MimicDB(namespace='tests')

        self.conn = S3Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        self.boto_conn = BotoS3Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

        self.redis = redis.StrictRedis()
        self.boto_bucket = self.boto_conn.create_bucket('mimicdb-tests')

        key = BotoKey(self.boto_bucket)
        key.key = 'upload'
        key.set_contents_from_string('upload')

    def tearDown(self):
        for bucket in self.boto_conn.get_all_buckets():
            if bucket.name.startswith('mimicdb-tests'):
                for key in bucket.list():
                    key.delete()

                bucket.delete()

        for key in self.redis.keys(tpl.connection + '*'):
            self.redis.delete(key)

    def redis_test(self):
        self.assertIsInstance(mimicdb.redis, redis.StrictRedis)

    def get_all_buckets_test(self):
        buckets = self.conn.get_all_buckets()

        assert buckets == []

    def get_all_buckets_force_test(self):
        buckets = self.conn.get_all_buckets(force=True)

        assert 'mimicdb-tests' in [bucket.name for bucket in buckets]
        assert 'mimicdb-tests' in self.redis.smembers(tpl.connection)

    def get_bucket_test(self):
        with self.assertRaises(S3ResponseError):
            self.conn.get_bucket('mimicdb-tests')

    def get_no_validate_bucket_test(self):
        self.conn.get_bucket('mimicdb-tests', validate=False)

    def get_bucket_force_test(self):
        self.conn.get_bucket('mimicdb-tests', force=True)

        assert 'mimicdb-tests' in self.redis.smembers(tpl.connection)

    def create_bucket_test(self):
        bucket = self.conn.create_bucket('mimicdb-tests-create')

        assert 'mimicdb-tests-create' in self.redis.smembers(tpl.connection)

    def delete_bucket_not_empty_test(self):
        self.conn.sync()

        try:
            self.conn.delete_bucket('mimicdb-tests')
        except S3ResponseError:
            pass

        assert 'mimicdb-tests' in self.redis.smembers(tpl.connection)

    def delete_bucket_empty_test(self):
        for key in self.boto_bucket.list():
            key.delete()

        self.conn.sync()
        self.conn.delete_bucket('mimicdb-tests')

        assert 'mimicdb-tests' not in self.redis.smembers(tpl.connection)

    def sync_test(self):
        self.conn.sync()

        assert 'mimicdb-tests' in self.redis.smembers(tpl.connection)
        assert 'upload' in self.redis.smembers(tpl.bucket % 'mimicdb-tests')

    def sync_bucket_test(self):
        self.boto_conn.create_bucket('mimicdb-tests-sync')

        self.conn.sync(buckets=['mimicdb-tests'])

        assert 'mimicdb-tests' in self.redis.smembers(tpl.connection)
        assert 'mimicdb-tests-sync' not in self.redis.smembers(tpl.connection)

    def sync_no_meta_test(self):
        self.conn.sync(metadata=False)

        meta = self.redis.hgetall(tpl.key % ('mimicdb-tests', 'upload'))

        assert meta == dict()

    def sync_meta_test(self):
        self.conn.sync(metadata=True)

        meta = self.redis.hgetall(tpl.key % ('mimicdb-tests', 'upload'))

        assert int(meta['size']) == len('upload')
        assert meta['md5'] == hashlib.md5('upload').hexdigest()

    def sync_clear_test(self):
        self.conn.sync(metadata=True)

        key = BotoKey(self.boto_bucket)
        key.key = 'upload'
        key.set_contents_from_string('sync_clear')

        self.conn.sync(metadata=True)

        meta = self.redis.hgetall(tpl.key % ('mimicdb-tests', 'upload'))

        assert int(meta['size']) == len('sync_clear')
        assert meta['md5'] == hashlib.md5('sync_clear').hexdigest()  

    def sync_bucket_clear_test(self):
        self.conn.sync(metadata=True)

        key = BotoKey(self.boto_bucket)
        key.key = 'upload'
        key.set_contents_from_string('sync_clear')

        self.conn.sync(metadata=True, buckets=['mimicdb-tests'])

        meta = self.redis.hgetall(tpl.key % ('mimicdb-tests', 'upload'))

        assert int(meta['size']) == len('sync_clear')
        assert meta['md5'] == hashlib.md5('sync_clear').hexdigest() 

    def get_unsynced_key_test(self):
        self.conn.sync()

        boto_key = BotoKey(self.boto_bucket)
        boto_key.name = 'get_key'
        boto_key.set_contents_from_string('get_key')

        bucket = self.conn.get_bucket('mimicdb-tests')
        key = bucket.get_key('get_key')

        assert key is None

    def get_unsynced_key_force_test(self):
        self.conn.sync()

        boto_key = BotoKey(self.boto_bucket)
        boto_key.name = 'get_key'
        boto_key.set_contents_from_string('get_key')

        bucket = self.conn.get_bucket('mimicdb-tests')
        key = bucket.get_key('get_key', force=True)

        assert key is not None

    def delete_keys_string_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket('mimicdb-tests')
        bucket.delete_keys(['upload'])

        boto_bucket = self.boto_conn.get_bucket('mimicdb-tests')
        key = boto_bucket.get_key('upload')

        assert key is None
        assert 'upload' not in self.redis.smembers(tpl.bucket % 'mimicdb-tests')

    def delete_keys_key_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket('mimicdb-tests')
        key = bucket.get_key('upload')
        bucket.delete_keys([key])

        boto_bucket = self.boto_conn.get_bucket('mimicdb-tests')
        key = boto_bucket.get_key('upload')

        assert key is None
        assert 'upload' not in self.redis.smembers(tpl.bucket % 'mimicdb-tests')

    def delete_key_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket('mimicdb-tests')
        bucket.delete_key('upload')

        key = self.boto_bucket.get_key('upload')

        assert key is None
        assert 'upload' not in self.redis.smembers(tpl.bucket % 'mimicdb-tests')

    def iter_test(self):
        self.conn.sync()

        key = BotoKey(self.boto_bucket)
        key.key = 'list'
        key.set_contents_from_string('list')

        bucket = self.conn.get_bucket('mimicdb-tests')

        assert 'list' not in [key.name for key in bucket]

    def list_test(self):
        self.conn.sync()

        key = BotoKey(self.boto_bucket)
        key.key = 'list'
        key.set_contents_from_string('list')

        bucket = self.conn.get_bucket('mimicdb-tests')
        keys = bucket.list()

        assert 'list' not in [key.name for key in keys]

    def list_force_no_meta_test(self):
        self.conn.sync()

        key = BotoKey(self.boto_bucket)
        key.key = 'list'
        key.set_contents_from_string('list')

        bucket = self.conn.get_bucket('mimicdb-tests')
        keys = bucket.list(force=True)

        assert 'list' in [key.name for key in keys]

    def list_force_meta_test(self):
        self.conn.sync(metadata=True)

        bucket = self.conn.get_bucket('mimicdb-tests')
        keys = bucket.list()

        assert hashlib.md5('upload').hexdigest() in [key.md5 for key in keys]

    def get_all_test(self):
        self.conn.sync()
        bucket = self.conn.get_bucket('mimicdb-tests')

        assert 'upload' in [key.name for key in bucket.get_all_keys()]

    def get_all_force_test(self):
        self.conn.sync()

        boto_key = BotoKey(self.boto_bucket)
        boto_key.name = 'get_all'
        boto_key.set_contents_from_string('get_all')

        bucket = self.conn.get_bucket('mimicdb-tests')

        assert 'get_all' in [key.name for key in bucket.get_all_keys(force=True)]

    def bucket_sync_test(self):
        self.conn.sync()

        boto_key = BotoKey(self.boto_bucket)
        boto_key.name = 'sync'
        boto_key.set_contents_from_string('sync')

        bucket = self.conn.get_bucket('mimicdb-tests')
        bucket.sync()

        key = bucket.get_key('sync')

        assert key is not None

    def bucket_sync_no_meta_test(self):
        self.conn.sync()

        boto_key = BotoKey(self.boto_bucket)
        boto_key.name = 'sync'
        boto_key.set_contents_from_string('sync')

        bucket = self.conn.get_bucket('mimicdb-tests')
        bucket.sync(metadata=True)

        meta = self.redis.hgetall(tpl.key % ('mimicdb-tests', 'sync'))

        assert int(meta['size']) == len('sync')
        assert meta['md5'] == hashlib.md5('sync').hexdigest()  

    def bucket_sync_meta_test(self):
        self.conn.sync()

        boto_key = BotoKey(self.boto_bucket)
        boto_key.name = 'sync'
        boto_key.set_contents_from_string('sync')

        bucket = self.conn.get_bucket('mimicdb-tests')
        bucket.sync(metadata=False)

        meta = self.redis.hgetall(tpl.key % ('mimicdb-tests', 'sync'))

        assert meta == dict()

    def get_key_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket('mimicdb-tests')
        key = Key(bucket)
        key.key = 'upload'

        assert key.key == 'upload'

    def get_unassigned_key_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket('mimicdb-tests')
        key = Key(bucket)

        assert key.key == None

    def set_key_test(self):
        self.conn.sync(metadata=True)

        bucket = self.conn.get_bucket('mimicdb-tests')
        key = Key(bucket)
        key.key = 'upload'

        assert key.size == len('upload')
        assert key.md5 == hashlib.md5('upload').hexdigest()  

    def track_upload_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket('mimicdb-tests')

        key = Key(bucket)
        key.key = 'track'
        key.set_contents_from_string('track')

        assert 'track' in self.redis.smembers(tpl.bucket % 'mimicdb-tests')

    def track_upload_init_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket('mimicdb-tests')

        key = Key(bucket, 'track')
        key.set_contents_from_string('track')

        assert 'track' in self.redis.smembers(tpl.bucket % 'mimicdb-tests')

    def track_upload_meta_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket('mimicdb-tests')

        key = Key(bucket)
        key.key = 'track'
        key.set_contents_from_string('track')

        meta = self.redis.hgetall(tpl.key % ('mimicdb-tests', 'track'))

        assert int(meta['size']) == len('track')
        assert meta['md5'] == hashlib.md5('track').hexdigest()

    def track_upload_meta_init_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket('mimicdb-tests')

        key = Key(bucket, 'track')
        key.set_contents_from_string('track')

        meta = self.redis.hgetall(tpl.key % ('mimicdb-tests', 'track'))

        assert int(meta['size']) == len('track')
        assert meta['md5'] == hashlib.md5('track').hexdigest()

    def track_download_meta_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket('mimicdb-tests')

        key = BotoKey(self.boto_bucket)
        key.key = 'download'
        key.set_contents_from_string('download')

        key = Key(bucket)
        key.key = 'download'
        key.get_contents_as_string()

        meta = self.redis.hgetall(tpl.key % ('mimicdb-tests', 'download'))

        assert int(meta['size']) == len('download')
        assert meta['md5'] == hashlib.md5('download').hexdigest()

    def track_download_meta_init_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket('mimicdb-tests')

        key = BotoKey(self.boto_bucket)
        key.key = 'download'
        key.set_contents_from_string('download')

        key = Key(bucket, 'download')
        key.get_contents_as_string()

        meta = self.redis.hgetall(tpl.key % ('mimicdb-tests', 'download'))

        assert int(meta['size']) == len('download')
        assert meta['md5'] == hashlib.md5('download').hexdigest()
