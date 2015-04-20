"""MimicDB Key subclass wrapper
"""

import re

from boto.s3.key import Key as BotoKey

import mimicdb

from ..backends import tpl


class Key(BotoKey):
    def __init__(self, *args, **kwargs):
        """Add the key to the bucket set if the key name is set and metadata is
        available for it, otherwise wait until uploaded or downloaded.
        """
        bucket = kwargs.get('bucket', args[0] if args else None)
        name = kwargs.get('name', args[1] if len(args) > 1 else None)

        self._name = name

        if name and bucket:
            meta = mimicdb.backend.hgetall(tpl.key % (bucket.name, name))

            if meta:
                mimicdb.backend.sadd(tpl.bucket % bucket.name, name)
                self._load_meta(meta['size'], meta['md5'])

        super(Key, self).__init__(*args, **kwargs)

    def _load_meta(self, size, md5):
        """Set key attributes to retrived metadata. Might be extended in the
        future to support more attributes.
        """
        if not hasattr(self, 'local_hashes'):
            self.local_hashes = {}

        self.size = int(size)

        if (re.match('^"[a-fA-F0-9]{32}"$', md5)):
            self.md5 = md5

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        """Key name can be set by Key.key or Key.name. Key.key sets Key.name
        internally, so just handle this property. When changing the key
        name, try to load it's metadata from MimicDB. If it's not available,
        the key hasn't been uploaded, downloaded or synced so don't add it to
        the bucket set (it also might have just been deleted,
        see boto.s3.bucket.py#785)
        """
        self._name = value

        if value:
            meta = mimicdb.backend.hgetall(tpl.key % (self.bucket.name, value))

            if meta:
                mimicdb.backend.sadd(tpl.bucket % self.bucket.name, value)
                self._load_meta(meta['size'], meta['md5'])

    def _send_file_internal(self, *args, **kwargs):
        """Called internally for any type of upload. After upload finishes,
        make sure the key is in the bucket set and save the metadata.
        """
        super(Key, self)._send_file_internal(*args, **kwargs)

        mimicdb.backend.sadd(tpl.bucket % self.bucket.name, self.name)
        mimicdb.backend.hmset(tpl.key % (self.bucket.name, self.name),
                            dict(size=self.size, md5=self.md5))

    def _get_file_internal(self, *args, **kwargs):
        """Called internally for any type of download. After download finishes,
        make sure the key is in the bucket set and save the metadata.
        """
        super(Key, self)._get_file_internal(*args, **kwargs)

        mimicdb.backend.sadd(tpl.bucket % self.bucket.name, self.name)
        mimicdb.backend.hmset(tpl.key % (self.bucket.name, self.name),
                            dict(size=self.size, md5=self.md5))        
