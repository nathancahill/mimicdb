import os
import random
import string
import hashlib
import logging
import unittest

from boto.s3.connection import S3Connection as BotoS3Connection
from boto.s3.bucket import Bucket as BotoBucket
from boto.s3.key import Key as BotoKey
from boto.exception import S3CreateError, S3ResponseError

import mimicdb
from mimicdb import MimicDB
from mimicdb.s3.connection import S3Connection
from mimicdb.s3.bucket import Bucket
from mimicdb.s3.key import Key
from mimicdb.backends import tpl
from mimicdb.backends.sqlite import SQLite

AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

logging.getLogger('boto').setLevel(logging.CRITICAL)

def random_string(size=6, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class MimicDBTestCase(unittest.TestCase):
    def setUp(self):
        MimicDB(SQLite())
        # MimicDB(namespace='tests')

        self.conn = S3Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        self.boto_conn = BotoS3Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

        self.name = 'mimicdb-tests-' + random_string()
        self.boto_bucket = self.boto_conn.create_bucket(self.name)

        key = BotoKey(self.boto_bucket)
        key.key = 'upload'
        key.set_contents_from_string('upload')

    def tearDown(self):
        for bucket in self.boto_conn.get_all_buckets():
            if bucket.name.startswith(self.name):
                for key in bucket.list():
                    key.delete()

                bucket.delete()

        for key in mimicdb.backend.keys(tpl.connection + '*'):
            mimicdb.backend.delete(key)

    def backend_test(self):
        self.assertIsInstance(mimicdb.backend, mimicdb.backends.Backend)

    def get_all_buckets_test(self):
        buckets = self.conn.get_all_buckets()

        assert buckets == []

    def get_all_buckets_force_test(self):
        buckets = self.conn.get_all_buckets(force=True)

        assert self.name in [bucket.name for bucket in buckets]

    def get_bucket_test(self):
        with self.assertRaises(S3ResponseError):
            self.conn.get_bucket(self.name)

    def get_no_validate_bucket_test(self):
        self.conn.get_bucket(self.name, validate=False)

    def get_bucket_force_test(self):
        self.conn.get_bucket(self.name, force=True)

        assert self.name in mimicdb.backend.smembers(tpl.connection)

    def create_bucket_test(self):
        bucket = self.conn.create_bucket(self.name + '-create')

        assert self.name + '-create' in mimicdb.backend.smembers(tpl.connection)

    def sync_test(self):
        self.conn.sync()

        assert self.name in mimicdb.backend.smembers(tpl.connection)
        assert 'upload' in mimicdb.backend.smembers(tpl.bucket % self.name)

        meta = mimicdb.backend.hgetall(tpl.key % (self.name, 'upload'))

        assert int(meta['size']) == len('upload')
        assert meta['md5'] == hashlib.md5('upload').hexdigest()

    def delete_bucket_not_empty_test(self):
        self.conn.sync()

        with self.assertRaises(S3ResponseError):
            self.conn.delete_bucket(self.name)

        assert self.name in mimicdb.backend.smembers(tpl.connection)

    def delete_bucket_empty_test(self):
        for key in self.boto_bucket.list():
            key.delete()

        self.conn.sync()
        self.conn.delete_bucket(self.name)

        assert self.name not in mimicdb.backend.smembers(tpl.connection)

    def sync_bucket_test(self):
        self.boto_conn.create_bucket(self.name + '-sync')

        self.conn.sync(self.name)

        assert self.name in mimicdb.backend.smembers(tpl.connection)
        assert self.name + '-sync' not in mimicdb.backend.smembers(tpl.connection)

    def sync_clear_test(self):
        self.conn.sync()

        key = BotoKey(self.boto_bucket)
        key.key = 'upload'
        key.set_contents_from_string('sync_clear')

        self.conn.sync()

        meta = mimicdb.backend.hgetall(tpl.key % (self.name, 'upload'))

        assert int(meta['size']) == len('sync_clear')
        assert meta['md5'] == hashlib.md5('sync_clear').hexdigest()  

    def sync_bucket_clear_test(self):
        self.conn.sync()

        key = BotoKey(self.boto_bucket)
        key.key = 'upload'
        key.set_contents_from_string('sync_clear')

        self.conn.sync(self.name)

        meta = mimicdb.backend.hgetall(tpl.key % (self.name, 'upload'))

        assert int(meta['size']) == len('sync_clear')
        assert meta['md5'] == hashlib.md5('sync_clear').hexdigest() 

    def get_unsynced_key_test(self):
        self.conn.sync()

        boto_key = BotoKey(self.boto_bucket)
        boto_key.name = 'get_key'
        boto_key.set_contents_from_string('get_key')

        bucket = self.conn.get_bucket(self.name)
        key = bucket.get_key('get_key')

        assert key is None

    def get_unsynced_key_force_test(self):
        self.conn.sync()

        boto_key = BotoKey(self.boto_bucket)
        boto_key.name = 'get_key'
        boto_key.set_contents_from_string('get_key')

        bucket = self.conn.get_bucket(self.name)
        key = bucket.get_key('get_key', force=True)

        assert key is not None

    def delete_keys_string_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket(self.name)
        bucket.delete_keys(['upload'])

        boto_bucket = self.boto_conn.get_bucket(self.name)
        key = boto_bucket.get_key('upload')

        assert key is None
        assert 'upload' not in mimicdb.backend.smembers(tpl.bucket % self.name)

    def delete_keys_key_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket(self.name)
        key = bucket.get_key('upload')
        bucket.delete_keys([key])

        boto_bucket = self.boto_conn.get_bucket(self.name)
        key = boto_bucket.get_key('upload')

        assert key is None
        assert 'upload' not in mimicdb.backend.smembers(tpl.bucket % self.name)

    def delete_key_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket(self.name)
        bucket.delete_key('upload')

        key = self.boto_bucket.get_key('upload')

        assert key is None
        assert 'upload' not in mimicdb.backend.smembers(tpl.bucket % self.name)

    def iter_test(self):
        self.conn.sync()

        key = BotoKey(self.boto_bucket)
        key.key = 'list'
        key.set_contents_from_string('list')

        bucket = self.conn.get_bucket(self.name)

        assert 'list' not in [key.name for key in bucket]

    def list_test(self):
        self.conn.sync()

        key = BotoKey(self.boto_bucket)
        key.key = 'list'
        key.set_contents_from_string('list')

        bucket = self.conn.get_bucket(self.name)
        keys = bucket.list()

        assert 'list' not in [key.name for key in keys]

    def list_force_test(self):
        self.conn.sync()

        key = BotoKey(self.boto_bucket)
        key.key = 'list'
        key.set_contents_from_string('list')

        bucket = self.conn.get_bucket(self.name)
        keys = list(bucket.list(force=True))

        assert 'list' in [key.name for key in keys]
        assert hashlib.md5('list').hexdigest() in [key.md5 for key in keys]

    def get_all_test(self):
        self.conn.sync()
        bucket = self.conn.get_bucket(self.name)

        assert 'upload' in [key.name for key in bucket.get_all_keys()]

    def get_all_force_test(self):
        self.conn.sync()

        boto_key = BotoKey(self.boto_bucket)
        boto_key.name = 'get_all'
        boto_key.set_contents_from_string('get_all')

        bucket = self.conn.get_bucket(self.name)

        assert 'get_all' in [key.name for key in bucket.get_all_keys(force=True)]

    def bucket_sync_test(self):
        self.conn.sync()

        boto_key = BotoKey(self.boto_bucket)
        boto_key.name = 'sync'
        boto_key.set_contents_from_string('sync')

        bucket = self.conn.get_bucket(self.name)
        bucket.sync()

        key = bucket.get_key('sync')

        assert key.size == len('sync')
        assert key.md5 == hashlib.md5('sync').hexdigest()

    def get_key_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket(self.name)
        key = Key(bucket)
        key.key = 'upload'

        assert key.key == 'upload'

    def get_unassigned_key_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket(self.name)
        key = Key(bucket)

        assert key.key == None

    def set_key_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket(self.name)
        key = Key(bucket)
        key.key = 'upload'

        assert key.size == len('upload')
        assert key.md5 == hashlib.md5('upload').hexdigest()  

    def track_upload_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket(self.name)

        key = Key(bucket)
        key.key = 'track'
        key.set_contents_from_string('track')

        assert 'track' in mimicdb.backend.smembers(tpl.bucket % self.name)

    def track_upload_init_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket(self.name)

        key = Key(bucket, 'track')
        key.set_contents_from_string('track')

        assert 'track' in mimicdb.backend.smembers(tpl.bucket % self.name)

    def track_upload_meta_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket(self.name)

        key = Key(bucket)
        key.key = 'track'
        key.set_contents_from_string('track')

        meta = mimicdb.backend.hgetall(tpl.key % (self.name, 'track'))

        assert int(meta['size']) == len('track')
        assert meta['md5'] == hashlib.md5('track').hexdigest()

    def track_upload_meta_init_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket(self.name)

        key = Key(bucket, 'track')
        key.set_contents_from_string('track')

        meta = mimicdb.backend.hgetall(tpl.key % (self.name, 'track'))

        assert int(meta['size']) == len('track')
        assert meta['md5'] == hashlib.md5('track').hexdigest()

    def track_download_meta_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket(self.name)

        key = BotoKey(self.boto_bucket)
        key.key = 'download'
        key.set_contents_from_string('download')

        key = Key(bucket)
        key.key = 'download'
        key.get_contents_as_string()

        meta = mimicdb.backend.hgetall(tpl.key % (self.name, 'download'))

        assert int(meta['size']) == len('download')
        assert meta['md5'] == hashlib.md5('download').hexdigest()

    def track_download_meta_init_test(self):
        self.conn.sync()

        bucket = self.conn.get_bucket(self.name)

        key = BotoKey(self.boto_bucket)
        key.key = 'download'
        key.set_contents_from_string('download')

        key = Key(bucket, 'download')
        key.get_contents_as_string()

        meta = mimicdb.backend.hgetall(tpl.key % (self.name, 'download'))

        assert int(meta['size']) == len('download')
        assert meta['md5'] == hashlib.md5('download').hexdigest()
